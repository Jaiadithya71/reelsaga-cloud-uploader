import unittest
from unittest.mock import Mock
from credentials import GoogleCredentials, CredentialError
from adapters import Response

class CredentialTests(unittest.TestCase):
    def make(self):
        s=Mock();s.read.return_value={'client_id':'id','client_secret':'secret','refresh_token':'refresh','granted_scopes':['upload']}
        post=Mock(return_value=Response(200,{'access_token':'token','expires_in':3600,'token_type':'Bearer','scope':'upload'},{}))
        return GoogleCredentials(s,post,{'upload'},clock=lambda:100),s,post
    def test_cache_refresh_once(self):
        c,s,p=self.make();self.assertEqual(c.access_token(),'token');self.assertEqual(c.access_token(),'token');p.assert_called_once()
    def test_missing_scope_no_request(self):
        c,s,p=self.make();s.read.return_value['granted_scopes']=[]
        with self.assertRaises(CredentialError):c.access_token()
        p.assert_not_called()
    def test_invalid_grant_disables(self):
        c,s,p=self.make();p.return_value=Response(400,{'error':'invalid_grant'}, {})
        with self.assertRaises(CredentialError):c.access_token()
        with self.assertRaises(CredentialError):c.access_token()
        p.assert_called_once()
    def test_response_scope_missing_blocks(self):
        c,s,p=self.make();p.return_value.data['scope']='different'
        with self.assertRaises(CredentialError):c.access_token()
    def test_revoke_deletes_only_on_success(self):
        c,s,p=self.make();c.revoke();s.delete.assert_called_once()
        with self.assertRaises(CredentialError):c.access_token()
    def test_revoke_timeout_keeps_disabled_and_record(self):
        c,s,p=self.make();p.side_effect=RuntimeError('secret')
        with self.assertRaises(CredentialError) as ctx:c.revoke()
        self.assertNotIn('secret',str(ctx.exception));s.delete.assert_not_called()
        with self.assertRaises(CredentialError):c.access_token()
    def test_malformed_token_blocks(self):
        c,s,p=self.make();p.return_value.data['access_token']='a\nb'
        with self.assertRaises(CredentialError):c.access_token()
