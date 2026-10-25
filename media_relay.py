"""Prepared short-lived per-file media relay. Not deployed or publicly enabled.

Deployment must supply HTTPS, secrets and an explicit verified file catalog.
No directory routes. Opaque IDs only. Expiry and SHA256 verified on every fetch.
"""
import hashlib,hmac,time
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
class RelayError(RuntimeError):pass

class MediaRelay:
    def __init__(self,key,catalog,clock=time.time):
        if not isinstance(key,bytes) or len(key)<32:raise RelayError('Strong relay key required')
        self.key,self.catalog,self.clock=key,dict(catalog),clock
    def signature(self,item_id,expires):
        return hmac.new(self.key,f'{item_id}:{expires}'.encode(),hashlib.sha256).hexdigest()
    def url(self,origin,item_id,lifetime=3600):
        from urllib.parse import quote
        p=urlsplit(origin)
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in ('','/'):
            raise RelayError('HTTPS origin required')
        if item_id not in self.catalog or not 60<=lifetime<=7200:raise RelayError('Bounded file lifetime required')
        expires=int(self.clock())+lifetime
        return origin.rstrip('/')+'/media/'+quote(item_id,safe='')+'?expires='+str(expires)+'&signature='+self.signature(item_id,expires)
    def resolve(self,path,query):
        if not path.startswith('/media/') or path.count('/')!=2:raise RelayError('Unknown route')
        item_id=path.split('/')[-1]
        if item_id not in self.catalog:raise RelayError('Unknown file')
        q=parse_qs(query,strict_parsing=True)
        if set(q)!={'expires','signature'} or any(len(v)!=1 for v in q.values()):raise RelayError('Invalid query')
        expires=int(q['expires'][0]);now=self.clock()
        if expires<=now or expires>now+7200:raise RelayError('Expired or excessive lifetime')
        if not hmac.compare_digest(self.signature(item_id,expires),q['signature'][0]):raise RelayError('Invalid signature')
        item=self.catalog[item_id];p=Path(item['path'])
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise RelayError('Media changed')
        return p
    def __call__(self,environ,start_response):
        try:
            if environ.get('REQUEST_METHOD') not in ('GET','HEAD'):raise RelayError('Method not allowed')
            p=self.resolve(environ.get('PATH_INFO',''),environ.get('QUERY_STRING',''));size=p.stat().st_size
            headers=[('Content-Type','video/mp4'),('Content-Length',str(size)),('Cache-Control','private, no-store'),('X-Content-Type-Options','nosniff')]
            start_response('200 OK',headers)
            if environ['REQUEST_METHOD']=='HEAD':return []
            def stream():
                with p.open('rb') as f:
                    while True:
                        chunk=f.read(1024*1024)
                        if not chunk:break
                        yield chunk
            return stream()
        except Exception:
            start_response('404 Not Found',[('Content-Type','text/plain'),('Cache-Control','no-store')]);return [b'Not found']
