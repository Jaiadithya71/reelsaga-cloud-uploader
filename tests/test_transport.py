import unittest
from unittest.mock import Mock
from transport import Transport, NoRedirect
from adapters import RemoteError

class Result:
    code=200;headers={}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return b'{"id":"saved"}'
class TransportTests(unittest.TestCase):
    def make(self):
        o=Mock();o.open.return_value=Result()
        return Transport(lambda:'test-token',{'www.googleapis.com'},o),o
    def test_json_and_bearer(self):
        t,o=self.make();r=t('POST','https://www.googleapis.com/upload/youtube/v3/videos',json={'a':1})
        self.assertEqual(r.data,{'id':'saved'})
        self.assertEqual(o.open.call_args.args[0].get_header('Authorization'),'Bearer test-token')
    def test_foreign_origin_blocks_before_token(self):
        token=Mock();t=Transport(token,{'www.googleapis.com'})
        for url in ('http://www.googleapis.com/x','https://evil.test/x','https://www.googleapis.com.evil.test/x','https://u:p@www.googleapis.com/x','https://www.googleapis.com:444/x'):
            with self.assertRaises(RemoteError):t('GET',url)
        token.assert_not_called()
    def test_no_retry_and_secret_error_redacted(self):
        t,o=self.make();o.open.side_effect=RuntimeError('secret-session')
        with self.assertRaises(RemoteError) as ctx:t('GET','https://www.googleapis.com/x')
        self.assertNotIn('secret-session',str(ctx.exception));o.open.assert_called_once()
    def test_reject_header_override(self):
        t,o=self.make()
        with self.assertRaises(ValueError):t('GET','https://www.googleapis.com/x',headers={'authorization':'override'})
        o.open.assert_not_called()
    def test_no_redirect(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,'',{},'https://evil.test/'))
    def test_conflicting_body(self):
        t,o=self.make()
        with self.assertRaises(ValueError):t('POST','https://www.googleapis.com/x',json={},body=b'a')
        o.open.assert_not_called()

class TokenFormTests(unittest.TestCase):
    def test_exact_endpoint_and_no_bearer(self):
        from transport import GoogleTokenForms
        o=Mock();o.open.return_value=Result();f=GoogleTokenForms(o)
        f('https://oauth2.googleapis.com/token',{'grant_type':'refresh_token','refresh_token':'mock'})
        req=o.open.call_args.args[0]
        self.assertIsNone(req.get_header('Authorization'))
        self.assertIn(b'grant_type=refresh_token',req.data)
    def test_endpoint_query_rejected(self):
        from transport import GoogleTokenForms
        o=Mock()
        with self.assertRaises(RemoteError):GoogleTokenForms(o)('https://oauth2.googleapis.com/revoke?token=secret',{})
        o.open.assert_not_called()
