"""Offline quota guards. Tests must never contact Buffer."""
import contextlib,datetime,email.message,importlib.util,io,json,os,pathlib,tempfile,unittest,urllib.error
from unittest.mock import patch
class CooldownTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);(self.root/'ig-recovery').mkdir()
  source=pathlib.Path(__file__).with_name('buffer_client.py').read_text();target=self.root/'ig-recovery/buffer_client.py';target.write_text(source)
  spec=importlib.util.spec_from_file_location('isolated_buffer',target);self.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.mod)
  self.old=os.getcwd();os.chdir(self.root)
 def tearDown(self):os.chdir(self.old);self.tmp.cleanup()
 def stop(self,until): (self.root/'buffer-api-cooldown.json').write_text(json.dumps({'not_before':until}))
 def test_fresh_process_respects_saved_cooldown(self):
  self.stop('2999-01-01T00:00:00Z')
  with patch('urllib.request.urlopen')as call:
   for _ in range(2):
    with self.assertRaises(self.mod.Rejected):self.mod.Buffer('synthetic').post('saved-id')
   call.assert_not_called()
 def test_malformed_cooldown_fails_closed(self):
  self.stop('invalid')
  with patch('urllib.request.urlopen')as call:
   with self.assertRaises(self.mod.Rejected):self.mod.Buffer('synthetic').post('saved-id')
   call.assert_not_called()
 def test_repeated_headers_and_new_instance(self):
  h=email.message.Message();h['Retry-After']='120';h['RateLimit']='"15min"; r=2; t=60';h['RateLimit']='"30day"; r=0; t=120';h['Set-Cookie']='secret'
  e=urllib.error.HTTPError('https://api.buffer.com',429,'throttled',h,io.BytesIO(b'{"errors":[{"message":"never retain","extensions":{"code":"RATE_LIMIT_EXCEEDED","window":"30d"}}]}'))
  with patch('urllib.request.urlopen',side_effect=e)as call:
   b=self.mod.Buffer('synthetic-secret')
   for client in [b,b,self.mod.Buffer('synthetic-secret')]:
    with self.assertRaises(self.mod.Rejected):client.post('saved-id')
   self.assertEqual(call.call_count,1)
  data=json.loads(pathlib.Path('buffer-rate-limit-receipt.json').read_text());self.assertEqual(len(data[0]['headers']['RateLimit']),2)
  self.assertNotIn('secret',str(data));self.assertNotIn('never retain',str(data));self.assertEqual(data[0]['errors'][0]['window'],'30d')
 def test_expired_cooldown_allows_one_read(self):
  self.stop('2000-01-01T00:00:00Z')
  class Response:
   status=200;headers=email.message.Message()
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self):return b'{"data":{"post":{"id":"saved-id","status":"sent"}}}'
  with patch('urllib.request.urlopen',return_value=Response())as call:
   self.assertEqual(self.mod.Buffer('synthetic').post('saved-id')['status'],'sent');self.assertEqual(call.call_count,1)
 def test_non429_retains_http_class_without_body(self):
  e=urllib.error.HTTPError('https://api.buffer.com',403,'forbidden',email.message.Message(),io.BytesIO(b'private body'))
  with patch('urllib.request.urlopen',side_effect=e)as call:
   with self.assertRaisesRegex(self.mod.Uncertain,'HTTP 403'):self.mod.Buffer('synthetic').post('saved-id')
   self.assertEqual(call.call_count,1)
if __name__=='__main__':unittest.main()
