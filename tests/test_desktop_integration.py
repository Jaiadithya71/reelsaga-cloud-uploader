"""Offline loopback integration. No Google request or real keyring writes."""
import json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from urllib.parse import urlsplit,parse_qs,urlencode
from urllib.request import urlopen
from adapters import Response
import desktop_setup as setup

class DesktopIntegrationTests(unittest.TestCase):
    def run_case(self,channel=setup.CHANNEL):
        store=Mock();browser_results=[];threads=[]
        def browser(url):
            q=parse_qs(urlsplit(url).query)
            callback=q['redirect_uri'][0]+'?'+urlencode({'state':q['state'][0],'code':'offline-mock'})
            def send():
                with urlopen(callback) as r:browser_results.append(r.status)
            t=threading.Thread(target=send);t.start();threads.append(t);return True
        token=Mock(return_value=Response(200,{'access_token':'mock','refresh_token':'mock','token_type':'Bearer','scope':' '.join(setup.SCOPES)},{}))
        api=Mock(return_value=Response(200,{'items':[{'id':channel}]},{}))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'client.json';p.write_text(json.dumps({'installed':{'client_id':'mock','client_secret':'mock'}}))
            with patch('sys.argv',['setup','--client-json',str(p)]),patch.object(setup,'secure_keyring',return_value=store),patch('builtins.input',return_value='YES'),patch.object(setup.webbrowser,'open',side_effect=browser),patch.object(setup,'GoogleTokenForms',return_value=token),patch.object(setup,'Transport',return_value=api):
                try:setup.main()
                finally:
                    for t in threads:t.join(timeout=3)
        return store,token,api,browser_results
    def test_loopback_success_no_upload(self):
        store,token,api,res=self.run_case()
        self.assertEqual(res,[200]);store.set_password.assert_called_once();token.assert_called_once();api.assert_called_once()
        self.assertEqual(api.call_args.args[0],'GET')
        record=json.loads(store.set_password.call_args.args[2]);self.assertEqual(record['channel_id'],setup.CHANNEL)
    def test_wrong_channel_no_storage(self):
        with self.assertRaises(setup.SetupError):self.run_case('wrong-channel')
