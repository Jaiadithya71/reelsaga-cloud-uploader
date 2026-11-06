"""Read-only exact saved-post diagnosis. Never dispatch the publisher to inspect status.

Honors Buffer's saved cooldown in buffer_client before making one request.
No release, draft, edit, host cleanup, ledger update or queue advancement.
"""
import json,os,pathlib
from buffer_client import Buffer,Rejected
POST_ID='6aec10813ddb81d22107892b'
CHANNEL_ID='6adb4d02778b240e2f9c6d48'
def inspect(buffer):
 post=buffer.post(POST_ID)
 if post.get('id')!=POST_ID or post.get('channelId')!=CHANNEL_ID:
  raise Rejected('Saved post identity/channel mismatch; no mutation')
 return {'post_id':post['id'],'channel_id':post['channelId'],'status':post.get('status'),'sent_at':post.get('sentAt'),'external_link':post.get('externalLink'),'caption':post.get('text'),'metadata':post.get('metadata'),'read_only':True,'queue_advanced':False}
if __name__=='__main__':
 os.chdir(pathlib.Path(__file__).resolve().parent.parent)
 print(json.dumps(inspect(Buffer(os.environ.pop('REELSAGA_BUFFER_API_KEY'))),indent=2))
