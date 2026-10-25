import unittest
from urllib.parse import urlsplit,parse_qs
from oauth_flow import OAuthAttempt, OAuthFlowError
class OAuthTests(unittest.TestCase):
    def make(self):return OAuthAttempt('mock-client','http://127.0.0.1:4567',['upload'])
    def test_pkce_state_unique(self):
        a,b=self.make(),self.make();self.assertNotEqual(a.state,b.state);self.assertNotEqual(a.verifier,b.verifier)
        q=parse_qs(urlsplit(a.authorization_url()).query);self.assertEqual(q['code_challenge_method'],['S256']);self.assertNotIn(a.verifier,a.authorization_url())
    def test_wrong_state_no_exchange(self):
        a=self.make()
        with self.assertRaises(OAuthFlowError):a.accept_callback('wrong','code')
        self.assertFalse(a.used)
    def test_callback_once(self):
        a=self.make();self.assertEqual(a.accept_callback(a.state,'mock')['code_verifier'],a.verifier)
        with self.assertRaises(OAuthFlowError):a.accept_callback(a.state,'mock')
    def test_denied_consumes_attempt(self):
        a=self.make()
        with self.assertRaises(OAuthFlowError):a.accept_callback(a.state,None,error='access_denied')
        self.assertTrue(a.used)
    def test_unapproved_http_blocks(self):
        for u in ['http://public.test/callback','https://user:secret@public.test/callback','https://public.test/callback#fragment']:
            with self.assertRaises(OAuthFlowError):OAuthAttempt('mock',u,['upload'])
