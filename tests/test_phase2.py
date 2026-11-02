"""Flask workflow tests use repository mocks, never the real database."""
import unittest
from unittest.mock import patch
from werkzeug.security import generate_password_hash
from app import create_app


class Phase6RouteTests(unittest.TestCase):
    def setUp(self):
        self.app=create_app(); self.app.config.update(TESTING=True,SECRET_KEY='test-only')
        self.client=self.app.test_client()
        self.user={'id':'u1','name':'Admin','email':'admin@example.test','role':'admin','password_hash':generate_password_hash('secret1'),'college':None,'roll_number':None}

    def session(self,role='admin'):
        with self.client.session_transaction() as s: s.update(user_id='u1',role=role,name='Admin',email='admin@example.test')

    @patch('data.get_user_by_email')
    def test_login_uses_hash(self, lookup):
        lookup.return_value=self.user
        self.assertIn(b'admin/dashboard',self.client.post('/login',data={'email':'admin@example.test','password':'secret1'}).data)
        self.client.get('/logout')
        self.assertIn(b'Invalid email or password',self.client.post('/login',data={'email':'admin@example.test','password':'wrong'}).data)

    @patch('data.save_event')
    def test_event_post_uses_repository_and_permission(self, save):
        self.session('participant')
        self.client.post('/admin/events',data={'action':'create','name':'Test'})
        save.assert_not_called()
        self.session('admin')
        self.client.post('/admin/events',data={'action':'create','name':'Test'})
        save.assert_called_once()

    @patch('data.register')
    def test_registration_post_calls_repository(self, register):
        self.session()
        self.client.post('/admin/data-entry',data={'entry_type':'registration','participantId':'u1','eventId':'e1','itemIds':['i1','i2']})
        register.assert_called_once_with('u1','e1',['i1','i2'])

    @patch('data.save_club')
    @patch('data.save_venue')
    def test_club_and_venue_writes_use_repository(self, venue, club):
        self.session()
        self.client.post('/admin/clubs',data={'action':'create','name':'Club'})
        self.client.post('/admin/venues',data={'action':'create','name':'Hall'})
        club.assert_called_once(); venue.assert_called_once_with('Hall',None)

    @patch('data.register')
    @patch('data.get_events',return_value=[])
    @patch('data.get_user_by_id',return_value={'id':'u1','assigned_events':['e1']})
    def test_manager_cannot_register_for_unassigned_event(self, user, events, register):
        self.session('manager')
        self.client.post('/manager/participants',data={'eventId':'e2','itemIds':'i1'})
        register.assert_not_called()

    @patch('data.save_item_result')
    def test_result_post_uses_repository(self, save):
        self.session()
        self.client.post('/admin/results',data={'action':'save_item_result','eventId':'e1','itemId':'i1','participantId':'u1','rank':'1','score':'95','medal':'Gold','published':'on'})
        save.assert_called_once_with('e1','i1','u1','1','95','Gold',True)


if __name__ == '__main__': unittest.main()
