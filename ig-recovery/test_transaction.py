import unittest
from transaction import Transaction
class State:
 def __init__(self):self.events=[]
 def claim(self,i):self.events.append('claim');return True
 def checkpoint(self,i,s,**kw):self.events.append((s,kw))
 def save_host(self,i,h):self.events.append('saved_host')
class Host:
 def stage(self,i,s):return {'url':'https://fixture.invalid/video'}
 def cleanup(self,i):pass
 def absent(self,i):return True
class Buffer:
 def draft(self,*a):return {'post':{'id':'p'}}
 def release(self,*a):return {'post':{'id':'p'}}
 def post(self,p):return {'id':p,'status':'sent','externalLink':'https://fixture.invalid/p'}
class Tests(unittest.TestCase):
 def setUp(self):self.s=State();self.b=Buffer();self.h=Host();self.t=Transaction(self.s,self.b,self.h);self.i={'cover_ms':2000}
 def test_claim_before_host(self):self.t.prepare(self.i,'c','file',True);self.assertEqual(self.s.events[0],'claim');self.assertEqual(self.s.events[-1][0],'ready_for_review')
 def test_uncertain_no_retry(self):
  self.b.draft=lambda *a:(_ for _ in()).throw(RuntimeError('timeout'))
  with self.assertRaises(RuntimeError):self.t.prepare(self.i,'c','file',True)
  self.assertEqual(self.s.events[-1][0],'uncertain')
 def test_publish_only_after_absence(self):
  self.h.absent=lambda i:False
  with self.assertRaises(RuntimeError):self.t.finish(self.i,'p',self.b.post('p'),True)
  self.assertNotEqual(self.s.events[-1][0],'published')
 def test_pixels_required(self):
  with self.assertRaises(RuntimeError):self.t.finish(self.i,'p',self.b.post('p'),False)
  self.assertEqual(self.s.events,[])
 def test_complete(self):self.t.finish(self.i,'p',self.b.post('p'),True);self.assertEqual(self.s.events[-1][0],'published')
if __name__=='__main__':unittest.main()
