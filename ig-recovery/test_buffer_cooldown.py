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
 def quota_receipt(self,remaining=300,total=3000,seconds=3600):
  event={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http_status':200,'headers':{'RateLimit':[f'"quota-30d";r={remaining};t={seconds}'],'RateLimit-Policy':[f'"quota-30d";q={total};w=2592000']}}
  pathlib.Path('buffer-rate-limit-receipt.json').write_text(json.dumps([event]));return event
 def test_low_success_budget_blocks_fresh_instance(self):
  self.quota_receipt()
  with patch('urllib.request.urlopen')as call:
   with self.assertRaisesRegex(self.mod.Rejected,'ten percent'):self.mod.Buffer('synthetic').post('saved-id')
   call.assert_not_called()
 def test_above_threshold_is_not_low(self):
  self.assertIsNone(self.mod.Buffer.low_budget_until(self.quota_receipt(301)))
 def test_missing_policy_is_not_fabricated(self):
  e=self.quota_receipt();del e['headers']['RateLimit-Policy'];self.assertIsNone(self.mod.Buffer.low_budget_until(e))
 def test_multiple_combined_policies(self):
  e=self.quota_receipt();e['headers']={'RateLimit':'"arbitrary";r=10;t=40, "long";r=299;t=900','RateLimit-Policy':'"arbitrary";q=150;w=900, "long";q=3000;w=2592000'}
  until=self.mod.Buffer.low_budget_until(e);self.assertAlmostEqual((until-datetime.datetime.fromisoformat(e['at'])).total_seconds(),900)
 def test_expired_headroom_receipt_does_not_lock_forever(self):
  e=self.quota_receipt(seconds=1);e['at']='2000-01-01T00:00:00+00:00';pathlib.Path('buffer-rate-limit-receipt.json').write_text(json.dumps([e]))
  class Response:
   status=200;headers=email.message.Message()
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self):return b'{"data":{"post":{"id":"saved-id"}}}'
  with patch('urllib.request.urlopen',return_value=Response())as call:
   self.mod.Buffer('synthetic').post('saved-id');self.assertEqual(call.call_count,1)
 def test_run_budget_bounds_even_missing_headers(self):
  class Response:
   status=200;headers=email.message.Message()
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self):return b'{"data":{"post":{"id":"saved-id"}}}'
  with patch('urllib.request.urlopen',return_value=Response())as call:
   b=self.mod.Buffer('synthetic')
   for _ in range(25):b.post('saved-id')
   with self.assertRaisesRegex(self.mod.Rejected,'Per-run'):b.post('saved-id')
   self.assertEqual(call.call_count,25)
if __name__=='__main__':unittest.main()
