"""Transactional publishing leg. Host and pixels are explicit injected gates."""
from queue_guard import require
class Transaction:
 def __init__(self,state,buffer,host):self.s,self.b,self.h=state,buffer,host
 def prepare(self,item,caption,source,verified_preflight):
  require(verified_preflight is True,'Preflight missing');require(self.s.claim(item),'Existing claim; reconcile')
  self.s.checkpoint(item,'uploading',session='host_intent')
  # Host implementation must persist deterministic locator before upload, never retry.
  host=self.h.stage(item,source);self.s.save_host(item,host)
  self.s.checkpoint(item,'uncertain',session='buffer_create_draft')
  r=self.b.draft('6adb4d02778b240e2f9c6d48',caption,host['url'],item['cover_ms'])
  require(r.get('post',{}).get('id'),'Draft rejected; reconcile existing inventory')
  pid=r['post']['id'];self.s.checkpoint(item,'ready_for_review',external_id=pid,session='draft_pixels_pending');return pid
 def release(self,item,pid,caption,host,verified_draft):
  require(verified_draft is True,'Exact draft/current identity/full-height cover not verified')
  self.s.checkpoint(item,'uncertain',external_id=pid,session='release_existing_draft')
  r=self.b.release(pid,caption,host['url'],item['cover_ms']);require(r.get('post',{}).get('id')==pid,'Release not acknowledged; reconcile')
  return self.b.post(pid)
 def finish(self,item,pid,post,public_pixels_verified):
  require(post.get('id')==pid and post.get('status')=='sent'and post.get('externalLink'),'Publication not confirmed')
  require(public_pixels_verified is True,'Actual public playback/cover not verified')
  self.s.checkpoint(item,'ready_for_review',external_id=pid,session='sent_pixels_verified_cleanup_pending')
  self.h.cleanup(item);require(self.h.absent(item)is True,'Host or delivery still accessible')
  self.s.checkpoint(item,'published',external_id=pid,session='public_pixels_verified_host_absent')
