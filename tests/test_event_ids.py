"""Sequential event allocation tests with isolated, concurrent fake connections."""
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from unittest.mock import patch

import data


class FakeDatabase:
    def __init__(self, ids):
        self.ids = list(ids)
        self.lock = threading.Lock()

    @contextmanager
    def cursor(self, write=False):
        cursor = FakeCursor(self)
        try:
            yield cursor
            if cursor.pending:
                self.ids.append(cursor.pending)  # commit while the advisory lock is held
        finally:
            if cursor.held:
                self.lock.release()  # connection close releases MySQL advisory locks


class FakeCursor:
    def __init__(self, db):
        self.db = db
        self.held = False
        self.pending = None
        self.result = None

    def execute(self, sql, params=()):
        if 'SELECT venue_id' in sql:
            self.result = {'venue_id': 'v1'}
        elif 'GET_LOCK' in sql:
            self.held = self.db.lock.acquire(timeout=2)
            self.result = {'acquired': int(self.held)}
        elif 'SELECT event_id FROM events' in sql:
            assert self.held and 'FOR UPDATE' in sql
            self.result = [{'event_id': value} for value in self.db.ids
                           if value.startswith('e') and value[1:].isascii()
                           and value[1:].isdigit()]
        elif 'INSERT INTO events' in sql:
            assert self.held
            self.pending = params[0]
            if self.pending in self.db.ids:
                raise AssertionError('duplicate ID')
        else:
            raise AssertionError(sql)

    def fetchone(self): return self.result
    def fetchall(self): return self.result


class EventIdTests(unittest.TestCase):
    values = {'name': 'Test', 'date': '2027-01-01', 'venue': 'Hall'}

    def test_sequence_ignores_uuid_records_and_starts_at_four(self):
        db = FakeDatabase(['e1', 'e2', 'ead78f839e3714ab79273e3b8de578616'])
        with patch.object(data, 'cursor', db.cursor):
            for _ in range(3): data.save_event(self.values)
        self.assertEqual(db.ids[-3:], ['e4', 'e5', 'e6'])
        self.assertIn('ead78f839e3714ab79273e3b8de578616', db.ids)

    def test_existing_higher_numeric_id_is_respected(self):
        db = FakeDatabase(['e1', 'e18', 'e0009', 'eabc123'])
        with patch.object(data, 'cursor', db.cursor): data.save_event(self.values)
        self.assertEqual(db.ids[-1], 'e19')

    def test_concurrent_creations_have_unique_sequential_ids(self):
        db = FakeDatabase(['e1', 'e2'])
        with patch.object(data, 'cursor', db.cursor):
            with ThreadPoolExecutor(max_workers=10) as executor:
                list(executor.map(lambda _: data.save_event(self.values), range(25)))
        self.assertEqual(set(db.ids[2:]), {f'e{i}' for i in range(4, 29)})

    def test_lock_failure_does_not_insert(self):
        class BusyCursor:
            def execute(self, sql, params): pass
            def fetchone(self): return {'acquired': 0}
        with self.assertRaisesRegex(ValueError, 'busy'):
            data.next_event_id(BusyCursor())


if __name__ == '__main__': unittest.main()
