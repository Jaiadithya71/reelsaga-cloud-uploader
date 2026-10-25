import unittest
from unittest.mock import Mock
from adapters import Response
from firestore_backend import FirestoreCAS, BackendError
class FirestoreTests(unittest.TestCase):
    def make(self):
        r=Mock();return FirestoreCAS(r,'candidate-project'),r
    def test_missing(self):
        b,r=self.make();r.return_value=Response(404,{},{});self.assertEqual(b.get('key'),(None,None))
    def test_get_record_and_version(self):
        b,r=self.make();r.return_value=Response(200,{'fields':{'record':{'stringValue':'{"state":"started"}'}},'updateTime':'v'},{});self.assertEqual(b.get('key'),({'state':'started'},'v'))
    def test_create_precondition(self):
        b,r=self.make();r.return_value=Response(200,{'updateTime':'v'},{});self.assertTrue(b.compare_and_swap('key',None,{}));self.assertEqual(r.call_args.kwargs['params'],{'currentDocument.exists':'false'})
    def test_update_precondition(self):
        b,r=self.make();r.return_value=Response(200,{'updateTime':'next'},{});b.compare_and_swap('key','v',{});self.assertEqual(r.call_args.kwargs['params'],{'currentDocument.updateTime':'v'})
    def test_conflict_no_retry(self):
        b,r=self.make();r.return_value=Response(412,{},{});self.assertFalse(b.compare_and_swap('key','v',{}));r.assert_called_once()
    def test_error_is_not_absence(self):
        b,r=self.make();r.return_value=Response(403,{},{});
        with self.assertRaises(BackendError):b.get('key')
    def test_missing_acknowledgement(self):
        b,r=self.make();r.return_value=Response(200,{},{});
        with self.assertRaises(BackendError):b.compare_and_swap('key','v',{})
