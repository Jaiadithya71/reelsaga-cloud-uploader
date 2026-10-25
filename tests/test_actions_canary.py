import tempfile,unittest
from unittest.mock import Mock
from actions_canary import run,ITEM
from tests.test_durable_state import MemoryCAS
from adapters import Response
from desktop_setup import CHANNEL
class CanaryTests(unittest.TestCase):
    def api(self):
        return Mock(side_effect=[Response(200,{}, {'Location':'https://www.googleapis.com/session/mock'}),Response(200,{'id':'mock-video'},{}),Response(200,{'items':[{'snippet':{'channelId':CHANNEL},'status':{'privacyStatus':'private'},'processingDetails':{'processingStatus':'succeeded'}}]}, {})])
    def test_single_private_canary(self):
        b=MemoryCAS();b.rows['account-control']=({'enabled':True},1)
        api=self.api()
        with tempfile.NamedTemporaryFile() as f:
            f.write(b'mockmedia');f.flush();r=run(b,api,f.name)
        self.assertEqual(r['privacy'],'private');self.assertFalse(r['public_publishing_enabled'])
        self.assertEqual(api.call_args_list[0].kwargs['json']['status']['privacyStatus'],'private')
        with self.assertRaises(RuntimeError):run(b,api,'unused')
        self.assertEqual(api.call_count,3)
    def test_stopped_no_platform_write(self):
        b=MemoryCAS();api=Mock()
        with self.assertRaises(Exception):run(b,api,'unused')
        api.assert_not_called()
    def test_checkpoint_failure_blocks_bytes(self):
        b=MemoryCAS();b.rows['account-control']=({'enabled':True},1)
        def api(method,url,**kwargs):
            b.fail=True
            return Response(200,{}, {'Location':'https://www.googleapis.com/session/mock'})
        with tempfile.NamedTemporaryFile() as f:
            f.write(b'mock');f.flush()
            with self.assertRaises(Exception):run(b,api,f.name)
