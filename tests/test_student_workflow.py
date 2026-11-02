"""Student route tests; repository is mocked and no database is changed."""
import unittest
from unittest.mock import patch
from app import create_app


class StudentWorkflowTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config.update(TESTING=True, SECRET_KEY='test')
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session.update(user_id='u1', role='participant', name='Student', email='s@example.test')
        self.student = {'id': 'u1', 'role': 'participant'}

    @patch('data.register', return_value=1)
    @patch('data.get_user_by_id')
    def test_post_uses_session_identity(self, user, register):
        user.return_value = self.student
        response = self.client.post('/participant/events/e1/register', data={'itemIds': 'i1', 'participant_id': 'other'})
        self.assertEqual(response.status_code, 302)
        register.assert_called_once_with('u1', 'e1', ['i1'])

    @patch('data.register')
    @patch('data.get_user_by_id', return_value={'id': 'u1', 'role': 'admin'})
    def test_stale_role_cannot_register(self, user, register):
        self.assertEqual(self.client.post('/participant/events/e1/register', data={'itemIds': 'i1'}).status_code, 403)
        register.assert_not_called()

    @patch('data.get_events')
    @patch('data.get_user_by_id')
    def test_browse_excludes_drafts(self, user, events):
        user.return_value = self.student
        events.return_value = [{'id': 'e1', 'name': 'Public', 'published': 1, 'date': '', 'venue': '', 'description': ''}, {'id': 'e2', 'name': 'Secret Draft', 'published': 0}]
        response = self.client.get('/participant/events')
        self.assertIn(b'Public', response.data)
        self.assertNotIn(b'Secret Draft', response.data)


if __name__ == '__main__': unittest.main()
