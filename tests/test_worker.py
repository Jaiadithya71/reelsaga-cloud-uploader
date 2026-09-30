import tempfile
import hashlib
import unittest
from unittest.mock import Mock
from worker import Worker, NeedsReview
from durable_state import DurableLedger, Conflict
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

    def test_new_youtube_success_path(self):
        w=self.make();item=dict(ITEM,sha256=hashlib.sha256(b'abc').hexdigest())
        w.drive.download.side_effect=lambda file_id,path:path.write_bytes(b'abc')
        def start(item,size,checkpoint):
            checkpoint('uploading',session='saved');return 'saved'
        def send(session,path,offset,checkpoint):
            checkpoint('private_locked',external_id='video');return {'video_id':'video'}
        w.youtube.start.side_effect=start;w.youtube.send_chunk.side_effect=send
        with tempfile.TemporaryDirectory() as d:self.assertEqual(w.run(item,'youtube',CATALOG,d),{'video_id':'video'})
        self.assertEqual(w.ledger.resume(item['id'],'youtube'),'do_not_create')
    def test_bad_hash_never_uploads(self):
        w=self.make();w.drive.download.side_effect=lambda file_id,path:path.write_bytes(b'bad')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):w.run(ITEM,'youtube',CATALOG,d)
        w.youtube.start.assert_not_called()
    def test_instagram_closed_gate_does_not_claim(self):
        w=self.make()
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(NeedsReview):w.run(ITEM,'instagram',CATALOG,d)
        self.assertEqual(w.ledger.resume(ITEM['id'],'instagram'),'unclaimed')
        w.drive.download.assert_not_called()

    def test_changed_hash_blocks_saved_session_resume(self):
        w=self.make();w.ledger.claim(ITEM,'youtube')
        w.ledger.checkpoint(ITEM['id'],'youtube','uploading',session='saved')
        item=dict(ITEM,sha256=hashlib.sha256(b'changed').hexdigest())
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(Conflict):w.run(item,'youtube',CATALOG,d)
        w.drive.download.assert_not_called();w.youtube.status.assert_not_called()
    def test_changed_caption_blocks_saved_container_resume(self):
        w=self.make();w.ledger.claim(ITEM,'instagram')
        w.ledger.checkpoint(ITEM['id'],'instagram','processing',external_id='saved')
        item=dict(ITEM,caption=ITEM['caption']+' additional words')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(Conflict):w.run(item,'instagram',CATALOG,d)
        w.instagram.status.assert_not_called();w.instagram.create.assert_not_called()
