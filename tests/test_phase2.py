import unittest

import data
from app import create_app


class Phase2Tests(unittest.TestCase):
    def setUp(self):
        self.snapshot = data.snapshot()
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def tearDown(self):
        for key, store in (("users", data.USERS), ("events", data.EVENTS), ("clubs", data.CLUBS), ("venues", data.VENUES), ("registrations", data.REGISTRATIONS), ("item_results", data.ITEM_RESULTS), ("event_results", data.EVENT_RESULTS)):
            store[:] = self.snapshot[key]

    def login(self, email, password):
        return self.client.post('/login', data={'email': email, 'password': password})

    def post(self, path, values):
        return self.client.post(path, data=values, follow_redirects=True)

    def test_demo_logins_and_role_restrictions(self):
        for email, password, home in [('admin@eventhub.edu', 'admin123', '/admin/dashboard'), ('priya@mit.edu', 'manager123', '/manager/dashboard'), ('ananya@student.edu', 'part123', '/participant/home')]:
            self.client.get('/logout')
            self.assertIn(home.encode(), self.login(email, password).data)
            self.assertEqual(self.client.get(home).status_code, 200)
        for path in ('/admin/clubs', '/admin/venues'):
            self.assertNotEqual(self.client.get(path).status_code, 200)
            self.post(path, {'action': 'create', 'name': 'Unauthorized'})
        self.assertFalse(data.CLUBS)
        self.assertFalse(any(v['name'] == 'Unauthorized' for v in data.VENUES))
        self.client.get('/logout')
        self.login('priya@mit.edu', 'manager123')
        self.assertNotEqual(self.client.get('/admin/clubs').status_code, 200)
        self.assertNotEqual(self.client.get('/admin/venues').status_code, 200)
        self.assertEqual(self.client.get('/manager/clubs').status_code, 200)

    def test_club_crud_and_coordinator_visibility(self):
        self.login('admin@eventhub.edu', 'admin123')
        self.post('/admin/clubs', {'action': 'create', 'name': ' Robotics ', 'description': 'Build', 'event_ids': 'e1', 'coordinator_ids': 'u2'})
        club = data.CLUBS[0]
        self.assertEqual(club['name'], 'Robotics')
        response = self.post('/admin/clubs', {'action': 'create', 'name': 'robotics'})
        self.assertIn(b'already exists', response.data)
        self.assertEqual(len(data.CLUBS), 1)
        self.assertIn(b'Robotics', self.client.get('/admin/events').data)
        self.assertIn(b'event associations', self.post('/admin/clubs', {'action': 'delete', 'id': club['id']}).data)
        self.client.get('/logout')
        self.login('priya@mit.edu', 'manager123')
        response = self.client.get('/manager/clubs')
        self.assertIn(b'Robotics', response.data)
        self.assertIn(b'Aether Tech Fest', response.data)
        self.assertIn(b'Robotics', self.client.get('/manager/events').data)
        self.client.get('/logout')
        self.login('admin@eventhub.edu', 'admin123')
        self.post('/admin/clubs', {'action': 'edit', 'id': club['id'], 'name': 'Arts', 'coordinator_ids': 'u3'})
        self.assertEqual(club['coordinator_ids'], ['u3'])
        self.post('/admin/clubs', {'action': 'delete', 'id': club['id']})
        self.assertFalse(data.CLUBS)
        self.assertIn(b'Select valid', self.post('/admin/clubs', {'action': 'create', 'name': 'Bad', 'event_ids': 'missing'}).data)

    def test_venues_and_event_entry(self):
        self.login('admin@eventhub.edu', 'admin123')
        self.post('/admin/venues', {'action': 'create', 'name': 'New Hall'})
        venue = next(v for v in data.VENUES if v['name'] == 'New Hall')
        self.assertIn(b'already exists', self.post('/admin/venues', {'action': 'create', 'name': 'new hall'}).data)
        self.assertIn(b'required', self.post('/admin/venues', {'action': 'create', 'name': '  '}).data)
        self.post('/admin/events', {'action': 'create', 'name': 'Test Event', 'date': '2027-01-01', 'venue': 'New Hall'})
        event = data.EVENTS[-1]
        self.assertEqual(event['venue'], 'New Hall')
        self.assertIn(b'still used', self.post('/admin/venues', {'action': 'delete', 'id': venue['id']}).data)
        self.post('/admin/venues', {'action': 'edit', 'id': venue['id'], 'name': 'Renamed Hall'})
        self.assertEqual(event['venue'], 'Renamed Hall')
        self.post('/admin/events', {'action': 'edit', 'id': event['id'], 'name': 'Edited', 'date': '2027-01-02', 'venue': 'Lab Block A'})
        self.assertEqual(event['venue'], 'Lab Block A')
        self.post('/admin/venues', {'action': 'delete', 'id': venue['id']})
        self.assertNotIn(venue, data.VENUES)
        activity_venue = next(v for v in data.VENUES if v['name'] == 'Sports Ground')
        self.assertIn(b'still used', self.post('/admin/venues', {'action': 'delete', 'id': activity_venue['id']}).data)
        self.post('/admin/venues', {'action': 'edit', 'id': activity_venue['id'], 'name': 'Playing Field'})
        self.assertEqual(data.EVENTS[0]['items'][1]['venue'], 'Playing Field')
        count = len(data.EVENTS)
        self.assertIn(b'valid venue', self.post('/admin/data-entry', {'entry_type': 'event', 'name': 'Bad', 'date': '2027-01-01', 'venue': 'Unknown'}).data)
        self.assertEqual(len(data.EVENTS), count)
        self.post('/admin/data-entry', {'entry_type': 'event', 'name': 'Good', 'date': '2027-01-01', 'venue': 'Lab Block A'})
        self.assertEqual(len(data.EVENTS), count + 1)
        self.post('/admin/events', {'action': 'delete', 'id': event['id']})
        self.assertNotIn(event, data.EVENTS)

    def test_existing_registration_activity_and_pages(self):
        self.login('admin@eventhub.edu', 'admin123')
        self.post('/admin/events/e1/items', {'action': 'create', 'name': 'Workshop', 'category': 'Tech', 'dateTime': '2027-01-01T10:00', 'venue': 'Another Location', 'maxParticipants': '10'})
        item = data.EVENTS[0]['items'][-1]
        self.assertEqual(item['venue'], 'Another Location')
        self.post('/admin/events/e1/items', {'action': 'edit', 'id': item['id'], 'name': 'Workshop 2', 'category': 'Tech', 'dateTime': '2027-01-01T10:00', 'venue': 'Elsewhere', 'maxParticipants': '10'})
        self.assertEqual(item['venue'], 'Elsewhere')
        self.post('/admin/events/e1/items', {'action': 'delete', 'id': item['id']})
        self.assertNotIn(item, data.EVENTS[0]['items'])
        self.post('/admin/team-managers', {'action': 'edit', 'id': 'u2', 'name': 'Priya Sharma', 'email': 'priya@mit.edu', 'college': 'MIT', 'assigned_events': 'e1'})
        self.assertEqual(data.get_user_by_id('u2')['assigned_events'], ['e1'])
        for path in ('/admin/results', '/admin/team-managers', '/admin/data-entry'):
            self.assertEqual(self.client.get(path).status_code, 200)
        self.client.get('/logout')
        self.login('priya@mit.edu', 'manager123')
        self.post('/manager/participants', {'name': 'New Student', 'email': 'new@example.com', 'college': 'MIT', 'roll_number': '123', 'eventId': 'e1', 'itemIds': 'i1'})
        student = data.get_user_by_email('new@example.com')
        self.assertTrue(any(r['participantId'] == student['id'] and 'i1' in r['itemIds'] for r in data.REGISTRATIONS))
        self.assertNotIn(b'Rhythm Cultural Night', self.client.get('/manager/events').data)
        for path in ('/manager/events', '/manager/schedule', '/manager/results', '/manager/profile'):
            self.assertEqual(self.client.get(path).status_code, 200)
        self.client.get('/logout')
        response = self.post('/register', {'name': 'Another', 'email': 'another@example.com', 'password': 'secret1', 'college': 'MIT', 'roll_number': '456'})
        self.assertIsNotNone(data.get_user_by_email('another@example.com'))
        self.login('ananya@student.edu', 'part123')
        for path in ('/participant/home', '/participant/schedule', '/participant/results', '/participant/profile'):
            self.assertEqual(self.client.get(path).status_code, 200)
        self.assertIn(b'CodeSprint', self.client.get('/participant/schedule').data)
        self.assertIn(b'Gold', self.client.get('/participant/results').data)


if __name__ == '__main__':
    unittest.main()
