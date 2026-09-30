import unittest,tempfile,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from media_relay import MediaRelay,RelayError
class RelayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'one.mp4';self.path.write_bytes(b'media')
        self.r=MediaRelay(b'x'*32,{'opaque-one':{'path':str(self.path),'sha256':hashlib.sha256(b'media').hexdigest()}},lambda:10000)
    def tearDown(self):self.tmp.cleanup()
    def parts(self,url=None):return urlsplit(url or self.r.url('https://example.test','opaque-one'))
    def test_signed_one_file(self):
        u=self.parts();self.assertEqual(self.r.resolve(u.path,u.query),self.path)
    def test_expired(self):
        u=self.parts();self.r.clock=lambda:14000
        with self.assertRaises(RelayError):self.r.resolve(u.path,u.query)
    def test_tamper_signature(self):
        u=self.parts()
        with self.assertRaises(RelayError):self.r.resolve(u.path,u.query.replace('signature=','signature=x'))
    def test_no_directory(self):
        with self.assertRaises(RelayError):self.r.resolve('/media/','')
    def test_no_path_traversal(self):
        with self.assertRaises(RelayError):self.r.resolve('/media/../../one.mp4','')
    def test_changed_media(self):
        u=self.parts();self.path.write_bytes(b'changed')
        with self.assertRaises(RelayError):self.r.resolve(u.path,u.query)
    def test_no_http(self):
        with self.assertRaises(RelayError):self.r.url('http://example.test','opaque-one')
    def test_limit_lifetime(self):
        with self.assertRaises(RelayError):self.r.url('https://example.test','opaque-one',86400)
    def test_wsgi_get_and_head(self):
        u=self.parts();status=[]
        for method in ('GET','HEAD'):
            body=b''.join(self.r({'REQUEST_METHOD':method,'PATH_INFO':u.path,'QUERY_STRING':u.query},lambda s,h:status.append(s)))
            self.assertEqual(body,b'media' if method=='GET' else b'')
        self.assertEqual(status,['200 OK','200 OK'])
    def test_weak_key(self):
        with self.assertRaises(RelayError):MediaRelay(b'weak',{})
