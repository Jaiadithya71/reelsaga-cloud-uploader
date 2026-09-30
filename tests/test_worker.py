import tempfile
import unittest
from unittest.mock import Mock
from worker import Worker, NeedsReview
from durable_state import DurableLedger
from test_durable_state import MemoryCAS
import test_queue
fixture=test_queue.QueueTests();fixture.setUp()
ITEM,CATALOG=fixture.item,fixture.catalog

class WorkerTests(unittest.TestCase):
    def make(self):
        return Worker(Mock(),Mock(),Mock(),DurableLedger(MemoryCAS()),Mock(),Mock())
    def test_completed_no_download(self):
        w=self.make();w.ledger.claim(ITEM,'youtube');w.ledger.checkpoint(ITEM['id'],'youtube','private_locked',external_id='v')
        with tempfile.TemporaryDirectory() as d:self.assertEqual(w.run(ITEM,'youtube',CATALOG,d),'do_not_create')
        w.drive.download.assert_not_called()
    def test_uncertain_no_recreation(self):
        w=self.make();w.ledger.claim(ITEM,'instagram');w.ledger.checkpoint(ITEM['id'],'instagram','uncertain',external_id='c')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(NeedsReview):w.run(ITEM,'instagram',CATALOG,d)
        w.instagram.create.assert_not_called()
    def test_wrong_destination_no_identity_or_download(self):
        w=self.make();item=dict(ITEM,youtube_channel_id='wrong')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):w.run(item,'youtube',CATALOG,d)
        w.check_identity.assert_not_called();w.drive.download.assert_not_called()
