"""Pure fail-closed checks shared by repair preparation and release."""
import datetime,hashlib
class GateError(RuntimeError):pass
def require(ok,why):
 if not ok:raise GateError(why)
def next_item(manifest,records):
 items=manifest['items'];require(len(items)==33,'Incomplete repair catalog')
 for i in items:
  state=records.get(i['id'])or{}
  if i.get('status')=='public_verified_cleaned':continue
  if state.get('state')=='published':continue
  require(state.get('state')not in ('started','uploading','processing','uncertain','ready_for_review'),'Existing in-flight item requires reconciliation')
  require(state.get('state')!='blocked','Prior blocked item must not be skipped')
  return i
 return None
def preflight(item,channel,recent,now,caption,min_gap=2400,rolling_cap=40):
 require(channel.get('id')=='6adb4d02778b240e2f9c6d48'and channel.get('organizationId')=='6adb4a329ef1e740831f7879'and channel.get('name','').lstrip('@')=='reelsaga3000','Wrong channel')
 require(not any(channel.get(k)for k in ('isDisconnected','isLocked','isQueuePaused')),'Channel not ready')
 require(hashlib.sha256(caption.encode()).hexdigest()==item['caption_sha256'],'Caption differs')
 require(getattr(recent,'complete',False)is True,'Complete paginated inventory required')
 used=0
 for p in recent:
  require(p.get('text','').strip()!=caption.strip(),'Existing caption needs reconciliation')
  ts=p.get('sentAt')or p.get('dueAt')
  if ts:
   t=datetime.datetime.fromisoformat(ts.replace('Z','+00:00'));age=(now-t).total_seconds()
   require(abs(age)>=min_gap,'Minimum spacing')
   if p.get('status')=='sent'and 0<=age<86400:used+=1
 require(used<rolling_cap,'Conservative rolling cap')
 return used
def media(item,probe):
 v=probe['video'];require(probe['bytes']==item['bytes']and probe['sha256']==item['sha256'],'Original hash or bytes differ')
 require(v['width']>0 and v['height']/v['width']>1.7,'Nonvertical original')
 require(v.get('sar')in('1:1','1/1'),'Unexpected pixel aspect')
 require(probe.get('audio_present')and probe.get('decode_ok'),'Missing audio or corrupt decode')
 require(1000<item['cover_ms']<v['durationMs']-1000,'Cover outside content')
 require(probe.get('cover_nonblack')and probe.get('pixels_reviewed'),'Full-height/cover pixels not verified')
 return True
def budget(usage,staged_bytes,next_bytes):
 require(usage.get('verified_free')is True and usage.get('card_present')is False,'Free/no-card state not verified')
 require(usage.get('bucket_is_separate')is True and usage.get('old_bucket_acl_off')is True,'Private sources not isolated')
 require(usage.get('class_a',10000)+100<9000 and usage.get('class_b',100000)+100<90000,'Request reserve exhausted')
 require(usage.get('inventory_bytes',4*1024**3)+staged_bytes+next_bytes+512*1024**2<4*1024**3,'Aggregate storage ceiling')
 require(usage.get('staged_count',2)<2,'Too many staged originals')
 return True
