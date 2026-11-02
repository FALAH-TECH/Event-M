"""Repository SQL tests use fake cursors; no database writes are performed."""
import unittest
from contextlib import contextmanager
from unittest.mock import Mock, patch
import data


class RepositoryTests(unittest.TestCase):
    def fake_cursor(self, answers):
        cur=Mock(); cur.fetchone.side_effect=answers
        @contextmanager
        def context(write=False): yield cur
        return cur, context

    def test_registration_validates_event_and_writes_both_tables(self):
        cur,context=self.fake_cursor([{'event_id':'e1'},{'user_id':'u1'},None,{'activity_id':'i1','max_participants':10}])
        cur.fetchall.return_value = []
        with patch.object(data,'cursor',context): data.register('u1','e1',['i1'])
        statements=[call.args[0] for call in cur.execute.call_args_list]
        self.assertTrue(any('INSERT INTO registrations ' in s for s in statements))
        self.assertTrue(any('INSERT INTO registration_activities ' in s for s in statements))
        self.assertTrue(any('activity_id=%s AND event_id=%s' in s for s in statements))

    def test_registration_rejects_activity_from_other_event(self):
        cur,context=self.fake_cursor([{'event_id':'e1'},{'user_id':'u1'},None,None])
        with patch.object(data,'cursor',context):
            with self.assertRaises(ValueError): data.register('u1','e1',['bad'])
        self.assertFalse(any('INSERT INTO registrations ' in call.args[0] for call in cur.execute.call_args_list))

    def test_event_insert_uses_venue_id_and_parameters(self):
        cur,context=self.fake_cursor([{'venue_id':'v1'}, {'acquired':1}])
        cur.fetchall.return_value = [{'event_id':'e1'}, {'event_id':'e2'}]
        with patch.object(data,'cursor',context): data.save_event({'name':'Test','date':'2027-01-01','venue':'Hall'})
        sql,params=cur.execute.call_args_list[-1].args
        self.assertIn('INSERT INTO events',sql); self.assertIn('%s',sql)
        self.assertIn('v1',params); self.assertIn('Test',params)

    def test_activity_and_schedule_share_transaction(self):
        cur,context=self.fake_cursor([{'venue_id':'v1'}])
        with patch.object(data,'cursor',context): data.save_item('e1',{'name':'Workshop','venue':'Hall','dateTime':'2027-01-01T10:00','maxParticipants':'10'})
        statements=[call.args[0] for call in cur.execute.call_args_list]
        self.assertTrue(any('INSERT INTO activities' in s for s in statements))
        self.assertTrue(any('INSERT INTO schedules' in s for s in statements))

    def test_results_use_publication_filter(self):
        with patch.object(data,'fetch',return_value=[]) as fetch:
            data.get_item_results('i1',published_only=True)
            self.assertIn('published=1',fetch.call_args.args[0])
            self.assertEqual(fetch.call_args.args[1],('i1',))


if __name__ == '__main__': unittest.main()
