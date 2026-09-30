import unittest,base64,hashlib
from unittest.mock import Mock
from github_state import GitHubState,StateError
from adapters import Response
class GitStateTests(unittest.TestCase):
    def roundtrip(self,newlines=False):
        saved={}
        def request(method,url,**kwargs):
            if method=='PUT':
                saved['raw']=base64.b64decode(kwargs['json']['content'])
                saved['sha']=hashlib.sha1(b'blob '+str(len(saved['raw'])).encode()+b'\x00'+saved['raw']).hexdigest()
                return Response(201,{'content':{'sha':saved['sha']}},{})
            if '/git/blobs/' in url:
                encoded=base64.b64encode(saved['raw']).decode()
                if newlines:encoded=encoded[:30]+'\n'+encoded[30:]+'\n'
                return Response(200,{'content':encoded,'sha':saved['sha'],'encoding':'base64'},{})
            return Response(200,{'content':'deliberately altered Contents payload','sha':saved['sha']},{})
        b=GitHubState(request,'mock-secret')
        self.assertTrue(b.compare_and_swap('item',None,{'session':'sensitive-url'}))
        self.assertNotIn(b'sensitive-url',saved['raw'])
        self.assertEqual(b.get('item'),({'session':'sensitive-url'},saved['sha']))
    def test_encrypt_roundtrip(self):self.roundtrip()
    def test_json_content_realistic_newlines(self):self.roundtrip(True)
    def test_stale_rejected(self):
        req=Mock(return_value=Response(409,{},{})); b=GitHubState(req,'mock')
        self.assertFalse(b.compare_and_swap('item','stale',{'state':'claim'}))
        self.assertEqual(req.call_args.kwargs['json']['sha'],'stale');self.assertEqual(req.call_count,1)
    def test_authentication_fails(self):
        raw=b'0'*40;sha=hashlib.sha1(b'blob 40\x00'+raw).hexdigest()
        req=Mock(side_effect=[Response(200,{'sha':sha},{}),Response(200,{'content':base64.b64encode(raw).decode(),'encoding':'base64'}, {})])
        with self.assertRaisesRegex(StateError,'AES-GCM'):GitHubState(req,'mock').get('item')
    def test_integrity_fails_before_decrypt(self):
        req=Mock(side_effect=[Response(200,{'sha':'0'*40},{}),Response(200,{'content':base64.b64encode(b'0'*40).decode(),'encoding':'base64'}, {})])
        with self.assertRaisesRegex(StateError,'integrity'):GitHubState(req,'mock').get('item')
    def test_forbidden_branch(self):
        with self.assertRaises(StateError):GitHubState(Mock(),'mock','main')
    def test_foreign_keys(self):
        with self.assertRaises(StateError):GitHubState(Mock(),'mock').get('../secret')
