"""Opt-in disposable MySQL fixtures. Requires an explicitly named isolated fixture DB.

Run with AETHER_TEST_DATABASE set; never points at the application's configured DB.
Tables and fixture rows are retained in the test DB for inspection.
"""
import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from unittest.mock import patch

import database
import data
from app import create_app


@unittest.skipUnless(os.getenv('AETHER_TEST_DATABASE'), 'isolated MySQL database not configured')
class RegistrationMySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        name = os.environ['AETHER_TEST_DATABASE']
        if name != 'devdb' or name == os.getenv('MYSQL_DATABASE', 'aether_db'):
            raise RuntimeError('Integration tests require isolated devdb, distinct from the application database')
        cls.env = patch.dict(os.environ, {'MYSQL_DATABASE': name})
        cls.env.start()
        with database.transaction() as conn:
            c = conn.cursor()
            c.execute('SHOW TABLES')
            tables = {row[0] for row in c.fetchall()}
            expected = {'colleges', 'users', 'venues', 'events', 'activities', 'schedules', 'registrations', 'registration_activities'}
            if tables and tables != expected:
                raise RuntimeError('Integration fixture database contains unexpected tables')
            cls.suffix = uuid4().hex[:8]
            statements = [
                'CREATE TABLE colleges (college_id VARCHAR(40) PRIMARY KEY, name VARCHAR(160) UNIQUE) ENGINE=InnoDB',
                "CREATE TABLE users (user_id VARCHAR(40) PRIMARY KEY, name VARCHAR(120), email VARCHAR(255) UNIQUE, password_hash VARCHAR(255), role VARCHAR(20), college_id VARCHAR(40), roll_number VARCHAR(40)) ENGINE=InnoDB",
                'CREATE TABLE venues (venue_id VARCHAR(40) PRIMARY KEY, venue_name VARCHAR(160)) ENGINE=InnoDB',
                'CREATE TABLE events (event_id VARCHAR(40) PRIMARY KEY, name VARCHAR(160), description TEXT, event_date DATE, banner VARCHAR(255), published BOOLEAN, venue_id VARCHAR(40)) ENGINE=InnoDB',
                'CREATE TABLE activities (activity_id VARCHAR(40) PRIMARY KEY, event_id VARCHAR(40), name VARCHAR(160), category VARCHAR(100), rules TEXT, max_participants INT, UNIQUE KEY (activity_id,event_id)) ENGINE=InnoDB',
                'CREATE TABLE schedules (activity_id VARCHAR(40) PRIMARY KEY, venue_id VARCHAR(40), starts_at DATETIME) ENGINE=InnoDB',
                "CREATE TABLE registrations (registration_id VARCHAR(40) PRIMARY KEY, participant_id VARCHAR(40), event_id VARCHAR(40), payment_status VARCHAR(20) DEFAULT 'pending', UNIQUE KEY (participant_id,event_id), UNIQUE KEY (registration_id,event_id)) ENGINE=InnoDB",
                'CREATE TABLE registration_activities (registration_id VARCHAR(40), activity_id VARCHAR(40), event_id VARCHAR(40), PRIMARY KEY (registration_id,activity_id), INDEX (activity_id,event_id), FOREIGN KEY (registration_id,event_id) REFERENCES registrations(registration_id,event_id), FOREIGN KEY (activity_id,event_id) REFERENCES activities(activity_id,event_id)) ENGINE=InnoDB',
            ]
            if not tables:
                for sql in statements: c.execute(sql)
            suffix = cls.suffix
            def ident(value): return value + suffix
            c.execute('INSERT INTO venues VALUES (%s,%s)', (ident('v1'), 'Hall'))
            for eid, published in [('e1', 1), ('e2', 0)]:
                c.execute('INSERT INTO events VALUES (%s,%s,%s,%s,NULL,%s,%s)', (ident(eid), 'Public' if published else 'Draft', 'Description', '2030-01-01', published, ident('v1')))
            for iid, eid, title, capacity in [('a1','e1','First',5), ('a2','e1','Second',5), ('a3','e1','Third',5), ('last','e1','Last seat',1), ('draft','e2','Draft',5)]:
                c.execute('INSERT INTO activities VALUES (%s,%s,%s,%s,%s,%s)', (ident(iid), ident(eid), title, 'Talk', 'Rules', capacity))
                c.execute('INSERT INTO schedules VALUES (%s,%s,%s)', (ident(iid), ident('v1'), '2030-01-01 10:00:00'))
            for uid in ('u1', 'u2', 'u3'):
                c.execute('INSERT INTO users VALUES (%s,%s,%s,%s,%s,NULL,NULL)', (ident(uid), uid, ident(uid)+'@example.test', 'hash', 'participant'))
            c.close()

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()

    def test_registration_and_last_seat_race(self):
        def ident(value): return value + self.suffix
        app = create_app(); app.config.update(TESTING=True, SECRET_KEY='test')
        client = app.test_client()
        with client.session_transaction() as session:
            session.update(user_id=ident('u1'), role='participant', name='u1', email='u1@example.test')
        self.assertIn(b'Public', client.get('/participant/events').data)
        self.assertNotIn(b'Draft', client.get('/participant/events').data)
        response = client.post('/participant/events/' + ident('e1') + '/register', data={'itemIds': ident('a1')}, follow_redirects=True)
        self.assertIn(b'Registration successful', response.data)
        self.assertIn(b'First', client.get('/participant/registrations').data)
        self.assertEqual(data.register(ident('u1'), ident('e1'), [ident('a1')]), 0)
        self.assertEqual(data.register(ident('u1'), ident('e1'), [ident('a2')]), 1)
        with self.assertRaises(ValueError): data.register(ident('u1'), ident('e2'), [ident('draft')])
        with self.assertRaises(ValueError): data.register(ident('u1'), ident('e1'), [ident('a1'), ident('draft')])
        barrier = threading.Barrier(2)
        def race(uid):
            barrier.wait()
            try:
                data.register(ident(uid), ident('e1'), [ident('last')])
                return 'success'
            except ValueError:
                return 'full'
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(race, ['u2', 'u3'])), ['success', 'full'])
        with self.assertRaises(ValueError):
            data.register(ident('u1'), ident('e1'), [ident('a3'), ident('last')])
        rows = data.fetch('SELECT r.participant_id, r.registration_id, ra.activity_id FROM registrations r JOIN registration_activities ra ON ra.registration_id=r.registration_id WHERE r.event_id=%s', (ident('e1'),))
        own = [r for r in rows if r['participant_id'] == ident('u1')]
        self.assertEqual({r['activity_id'] for r in own}, {ident('a1'), ident('a2')})
        self.assertEqual(len({r['registration_id'] for r in own}), 1)
        self.assertEqual(sum(r['activity_id'] == ident('last') for r in rows), 1)
        self.assertEqual(len(data.fetch('SELECT * FROM registrations WHERE event_id=%s', (ident('e1'),))), 2)


if __name__ == '__main__': unittest.main()
