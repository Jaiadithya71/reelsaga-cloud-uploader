import json,tempfile,unittest
from pathlib import Path
from desktop_setup import desktop_config,validate_tokens,SCOPES,SetupError
class DesktopTests(unittest.TestCase):
    def test_desktop_only(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'mock.json';p.write_text(json.dumps({'web':{'client_id':'id','client_secret':'mock'}}))
            with self.assertRaises(SetupError):desktop_config(p)
            p.write_text(json.dumps({'installed':{'client_id':'id','client_secret':'mock'}}))
            self.assertEqual(desktop_config(p)['client_id'],'id')
    def test_no_refresh_rejected(self):
        with self.assertRaises(SetupError):validate_tokens({'access_token':'mock'})
    def test_grant_complete(self):
        validate_tokens({'access_token':'mock','refresh_token':'mock','token_type':'Bearer','scope':' '.join(SCOPES)})
    def test_grant_subset_rejected(self):
        with self.assertRaises(SetupError):validate_tokens({'access_token':'mock','refresh_token':'mock','token_type':'Bearer','scope':SCOPES[0]})
