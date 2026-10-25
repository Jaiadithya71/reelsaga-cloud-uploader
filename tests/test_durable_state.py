import unittest
from durable_state import DurableLedger, Conflict

class MemoryCAS:
    def __init__(self): self.rows={}; self.fail=False
    def get(self,key):
        row,version=self.rows.get(key,(None,None)); return (dict(row) if row else None,version)
    def compare_and_swap(self,key,version,record):
        if self.fail or self.rows.get(key,(None,None))[1]!=version: return False
        self.rows[key]=(dict(record),(version or 0)+1); return True

class DurableTests(unittest.TestCase):
    def test_claim_once(self):
        ledger=DurableLedger(MemoryCAS()); item={'id':'one'}
        self.assertTrue(ledger.claim(item,'youtube')); self.assertFalse(ledger.claim(item,'youtube'))
    def test_metadata_change_blocks(self):
        ledger=DurableLedger(MemoryCAS());ledger.claim({'id':'one'},'youtube')
        with self.assertRaises(Conflict): ledger.claim({'id':'one','title':'changed'},'youtube')
    def test_failed_cas_blocks(self):
        backend=MemoryCAS(); backend.fail=True
        with self.assertRaises(Conflict): DurableLedger(backend).claim({'id':'one'},'youtube')
    def test_no_blind_resume(self):
        ledger=DurableLedger(MemoryCAS());ledger.claim({'id':'one'},'instagram')
        self.assertEqual(ledger.resume('one','instagram'),'reconcile_manually')
        ledger.checkpoint('one','instagram','uncertain',external_id='container')
        self.assertEqual(ledger.resume('one','instagram'),'reconcile_manually')
    def test_saved_session_resume(self):
        ledger=DurableLedger(MemoryCAS());ledger.claim({'id':'one'},'youtube')
        ledger.checkpoint('one','youtube','uploading',session='session')
        self.assertEqual(ledger.resume('one','youtube'),'query_saved_upload_session')
    def test_published_terminal(self):
        ledger=DurableLedger(MemoryCAS());ledger.claim({'id':'one'},'instagram');ledger.checkpoint('one','instagram','published',external_id='media')
        self.assertEqual(ledger.resume('one','instagram'),'do_not_create')
        with self.assertRaises(Conflict): ledger.checkpoint('one','instagram','started')
