"""Candidate Firestore REST CAS backend. Not selected or provisioned.

Requires dedicated IAM-authorized transport, not YouTube/Drive OAuth tokens.
No database or billing setup is performed by this module.
"""
import json
import re

class BackendError(RuntimeError):pass

class FirestoreCAS:
    def __init__(self, request, project, collection='reelsaga_state'):
        if not re.fullmatch(r'[a-z][a-z0-9-]{4,62}',project):raise ValueError('Invalid project')
        if not re.fullmatch(r'[a-zA-Z0-9_-]+',collection):raise ValueError('Invalid collection')
        self.request=request
        self.base=f'https://firestore.googleapis.com/v1/projects/{project}/databases/(default)/documents/{collection}/'
    def url(self,key):
        if not re.fullmatch(r'[a-zA-Z0-9_-]+',key):raise ValueError('Invalid key')
        return self.base+key
    def get(self,key):
        r=self.request('GET',self.url(key))
        if r.status==404:return None,None
        if r.status!=200:raise BackendError('State read failed; stop writes')
        try:
            record=json.loads(r.data['fields']['record']['stringValue'])
            version=r.data['updateTime']
        except (KeyError,ValueError,TypeError):
            raise BackendError('Invalid durable state') from None
        if not isinstance(record,dict) or not isinstance(version,str):raise BackendError('Invalid durable state')
        return record,version
    def compare_and_swap(self,key,version,record):
        params={'currentDocument.exists':'false'} if version is None else {'currentDocument.updateTime':version}
        r=self.request('PATCH',self.url(key),params=params,json={'fields':{'record':{'stringValue':json.dumps(record,sort_keys=True,separators=(',',':'))}}})
        if r.status in (409,412):return False
        if r.status!=200:raise BackendError('State update uncertain; stop external writes')
        if not r.data.get('updateTime'):raise BackendError('State acknowledgement missing')
        return True
