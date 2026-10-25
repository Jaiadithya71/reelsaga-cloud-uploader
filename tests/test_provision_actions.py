import json,unittest
from unittest.mock import Mock
from provision_actions import provision,ProvisionError
from desktop_setup import CHANNEL,SCOPES
class ProvisionTests(unittest.TestCase):
    def record(self):return json.dumps({'channel_id':CHANNEL,'granted_scopes':list(SCOPES),'client_id':'mock','client_secret':'hidden-mock','refresh_token':'refresh-mock'})
    def test_stdin_not_argv(self):
        run=Mock(return_value=Mock(returncode=0));provision(self.record(),run)
        argv=run.call_args.args[0];self.assertNotIn('hidden-mock',' '.join(argv));self.assertEqual(argv[0:3],['gh','secret','set']);self.assertIn('refresh-mock',run.call_args.kwargs['input'])
    def test_wrong_destination_no_call(self):
        run=Mock();data=json.loads(self.record());data['channel_id']='wrong'
        with self.assertRaises(ProvisionError):provision(json.dumps(data),run)
        run.assert_not_called()
    def test_failure_no_retry(self):
        run=Mock(return_value=Mock(returncode=1))
        with self.assertRaises(ProvisionError):provision(self.record(),run)
        run.assert_called_once()
