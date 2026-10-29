import hashlib,io,pathlib,tempfile,unittest
from unittest.mock import Mock
from botocore.exceptions import ClientError,ReadTimeoutError
from queue_guard import GateError
from verified_upload import put_once_verified
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.p=pathlib.Path(self.t.name)/'video';self.p.write_bytes(b'exact-video');self.sha=hashlib.sha256(self.p.read_bytes()).hexdigest();self.s=Mock();self.s.head_object.return_value={'ContentLength':11};self.s.get_object.return_value={'Body':io.BytesIO(b'exact-video')};self.s.get_object_acl.return_value={'Grants':[{'Grantee':{'URI':'http://acs.amazonaws.com/groups/global/AllUsers'},'Permission':'READ'}]}
 def tearDown(self):self.t.cleanup()
 def runput(self):return put_once_verified(self.s,'bucket','fresh-key',self.p,11,self.sha)
 def test_normal(self):self.assertFalse(self.runput()['ambiguous_ack_reconciled']);self.s.put_object.assert_called_once()
 def test_lost_ack_exact(self):
  self.s.put_object.side_effect=ClientError({'Error':{'Code':'PreconditionFailed'}},'PutObject');self.assertTrue(self.runput()['ambiguous_ack_reconciled']);self.s.put_object.assert_called_once()
 def test_timeout_landed(self):
  self.s.put_object.side_effect=ReadTimeoutError(endpoint_url='https://example.invalid');self.assertTrue(self.runput()['ambiguous_ack_reconciled']);self.s.put_object.assert_called_once()
 def test_wrong_size(self):
  self.s.head_object.return_value={'ContentLength':10}
  with self.assertRaises(GateError):self.runput()
  self.s.get_object.assert_not_called()
 def test_wrong_hash(self):
  self.s.get_object.return_value={'Body':io.BytesIO(b'wrong-video')}
  with self.assertRaises(GateError):self.runput()
  self.s.put_object.assert_called_once()
 def test_private(self):
  self.s.get_object_acl.return_value={'Grants':[]}
  with self.assertRaises(GateError):self.runput()
 def test_absent(self):
  self.s.put_object.side_effect=ClientError({'Error':{'Code':'PreconditionFailed'}},'PutObject');self.s.head_object.side_effect=ClientError({'Error':{'Code':'NoSuchKey'}},'HeadObject')
  with self.assertRaises(ClientError):self.runput()
  self.s.put_object.assert_called_once()
 def test_access_denied_not_reconciled(self):
  self.s.put_object.side_effect=ClientError({'Error':{'Code':'AccessDenied'}},'PutObject')
  with self.assertRaises(ClientError):self.runput()
  self.s.head_object.assert_not_called()
if __name__=='__main__':unittest.main()
