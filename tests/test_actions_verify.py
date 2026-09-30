import json, unittest
from unittest.mock import Mock
from actions_verify import verify, VerificationError
from desktop_setup import CHANNEL, SCOPES
from adapters import Response
class VerifyTests(unittest.TestCase):
    def record(self):
        return json.dumps(dict(channel_id=CHANNEL,granted_scopes=list(SCOPES),client_id='mock',client_secret='mock',refresh_token='mock'))
    def forms(self,scopes=None):
        return Mock(return_value=Response(200,dict(access_token='mock',token_type='Bearer',scope=' '.join(SCOPES if scopes is None else scopes)),{}))
    def test_success_only_get(self):
        api=Mock(return_value=Response(200,{'items':[{'id':CHANNEL}]},{}))
        result=verify(self.record(),self.forms(),lambda t:api)
        self.assertFalse(result['private_canary_uploaded']); self.assertFalse(result['publishing_enabled'])
        self.assertEqual(api.call_count,1); self.assertEqual(api.call_args.args[0],'GET')
    def test_missing_live_scope_stops(self):
        factory=Mock()
        with self.assertRaises(VerificationError):verify(self.record(),self.forms([]),factory)
        factory.assert_not_called()
    def test_wrong_channel_stops(self):
        api=Mock(return_value=Response(200,{'items':[{'id':'wrong'}]},{}))
        with self.assertRaises(VerificationError):verify(self.record(),self.forms(),lambda t:api)
    def test_invalid_secret_no_network(self):
        forms=Mock()
        with self.assertRaises(Exception):verify('{}',forms)
        forms.assert_not_called()
