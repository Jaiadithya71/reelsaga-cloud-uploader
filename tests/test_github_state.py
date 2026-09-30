import unittest,base64
from unittest.mock import Mock
from github_state import GitHubState,StateError
from adapters import Response
class GitStateTests(unittest.TestCase):
    def test_encrypt_roundtrip(self):
        calls=[]
        def request(method,url,**kwargs):
            calls.append((method,url,kwargs))
            if method=='PUT':return Response(201,{'content':{'sha':'version'}},{})
            return Response(200,{'content':calls[0][2]['json']['content'],'sha':'version'},{})
        backend=GitHubState(request,'mock-secret')
        self.assertTrue(backend.compare_and_swap('item',None,{'session':'sensitive-url'}))
        self.assertNotIn(b'sensitive-url',base64.b64decode(calls[0][2]['json']['content']))
        self.assertEqual(backend.get('item'),({'session':'sensitive-url'},'version'))
    def test_stale_rejected(self):
        req=Mock(return_value=Response(409,{},{})); b=GitHubState(req,'mock')
        self.assertFalse(b.compare_and_swap('item','stale',{'state':'claim'}))
        self.assertEqual(req.call_args.kwargs['json']['sha'],'stale');self.assertEqual(req.call_count,1)
    def test_authentication_fails(self):
        b=GitHubState(Mock(return_value=Response(200,{'content':base64.b64encode(b'invalid').decode(),'sha':'x'},{})),'mock')
        with self.assertRaises(StateError):b.get('item')
    def test_forbidden_branch(self):
        with self.assertRaises(StateError):GitHubState(Mock(),'mock','main')
    def test_foreign_keys(self):
        b=GitHubState(Mock(),'mock')
        with self.assertRaises(StateError):b.get('../secret')

    def test_json_content_realistic_newlines(self):
        calls=[]
        def request(method,url,**kwargs):
            calls.append((method,kwargs))
            if method=='PUT':return Response(201,{'content':{'sha':'x'}},{})
            encoded=calls[0][1]['json']['content']
            return Response(200,{'content':encoded[:30]+'\n'+encoded[30:]+'\n','sha':'x','encoding':'base64'},{})
        b=GitHubState(request,'mock')
        b.compare_and_swap('example',None,{'diagnostic':True})
        self.assertEqual(b.get('example')[0],{'diagnostic':True})
