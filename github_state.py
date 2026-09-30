"""Private repo Contents-API CAS ledger. All record payloads are AES-GCM encrypted.

Only a dedicated state branch is writable. No Actions artifacts or caches.
A stale Git blob SHA fails closed. Network uncertainty is never retried.
"""
import base64
import hashlib
import json
import os
import re
from adapters import checked

class StateError(RuntimeError): pass

class GitHubState:
    def __init__(self,request,key_material,branch='reelsaga-canary-state'):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        if branch!='reelsaga-canary-state':raise StateError('Unexpected state branch')
        if not key_material:raise StateError('Missing state encryption key')
        self.request=lambda method,url,**kw:request(method,url,headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2026-03-10'},**kw)
        self.branch=branch
        self.key=hashlib.sha256(b'reelsaga-state-v1\x00'+key_material.encode()).digest()
        self.aes=AESGCM(self.key)
        self.base='https://api.github.com/repos/Jaiadithya71/reelsaga-cloud-uploader'
    def initialize(self):
        r=self.request('GET',self.base+'/git/ref/heads/'+self.branch)
        if r.status==200:return
        if r.status!=404:raise StateError('State branch read failed')
        main=checked(self.request('GET',self.base+'/git/ref/heads/main')).data['object']['sha']
        checked(self.request('POST',self.base+'/git/refs',json={'ref':'refs/heads/'+self.branch,'sha':main}))
    def url(self,key):
        if not re.fullmatch(r'[a-zA-Z0-9_-]+',key):raise StateError('Invalid state key')
        return self.base+'/contents/state/'+key+'.enc'
    def get(self,key):
        r=self.request('GET',self.url(key),params={'ref':self.branch})
        if r.status==404:return None,None
        if r.status!=200:raise StateError('State read failed HTTP '+str(r.status))
        version=r.data.get('sha')
        if not isinstance(version,str) or not re.fullmatch(r'[0-9a-f]{40}',version):
            raise StateError('State blob SHA invalid')
        blob=self.request('GET',self.base+'/git/blobs/'+version)
        if blob.status!=200 or blob.data.get('encoding')!='base64':
            raise StateError('State immutable blob unavailable')
        try:
            raw=base64.b64decode(blob.data['content'])
        except Exception:raise StateError('State base64 decode failed') from None
        actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()
        if actual!=version:raise StateError('State blob integrity failed')
        if len(raw)<28:raise StateError('State ciphertext shorter than nonce plus tag')
        try:
            decrypted=self.aes.decrypt(raw[:12],raw[12:],key.encode())
        except Exception:raise StateError('State AES-GCM authentication failed') from None
        try:
            record=json.loads(decrypted)
            version=r.data['sha']
        except Exception:raise StateError('State decrypted JSON or SHA missing') from None
        if not isinstance(record,dict):raise StateError('Invalid state record')
        return record,version
    def compare_and_swap(self,key,version,record):
        nonce=os.urandom(12)
        payload=nonce+self.aes.encrypt(nonce,json.dumps(record,sort_keys=True).encode(),key.encode())
        body={'message':'Update encrypted canary checkpoint','content':base64.b64encode(payload).decode(),'branch':self.branch}
        if version is not None:body['sha']=version
        r=self.request('PUT',self.url(key),json=body)
        if r.status in (409,422):return False
        if r.status not in (200,201):raise StateError('State update uncertain; stop writes')
        if not r.data.get('content',{}).get('sha'):raise StateError('State acknowledgement missing')
        return True
