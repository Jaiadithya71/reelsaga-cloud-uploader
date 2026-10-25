import tempfile
import unittest
from pathlib import Path
from adapters import Drive, YouTube, Instagram, Response, RemoteError

class Mock:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []
    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.responses.pop(0)

def ok(data=None, status=200, headers=None, body=b''):
    return Response(status, data or {}, headers or {}, body)

class AdapterTests(unittest.TestCase):
    def test_youtube_always_private_and_checkpoint_session(self):
        request=Mock([ok(headers={'Location':'https://www.googleapis.com/upload/session'})])
        saved=[]
        session=YouTube(request).start({'title':'Title','description':'Exact'},12,lambda *a,**k:saved.append((a,k)))
        self.assertEqual(request.calls[0][1]['json']['status']['privacyStatus'],'private')
        self.assertEqual(saved[0][1]['session'],session)
    def test_youtube_no_unknown_session(self):
        request=Mock([ok(headers={'Location':'https://bad.invalid/x'})])
        with self.assertRaises(RemoteError): YouTube(request).start({'title':'T','description':'D'},12,lambda *a,**k:None)
    def test_youtube_resumption(self):
        request=Mock([ok(status=308,headers={'Range':'bytes=0-9'})])
        self.assertEqual(YouTube(request).status('saved',20),{'offset':10})
    def test_youtube_chunk_final_records_id(self):
        request=Mock([ok({'id':'video'})]); saved=[]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'test.mp4'; path.write_bytes(b'abc')
            result=YouTube(request).send_chunk('session',path,0,lambda *a,**k:saved.append((a,k)))
        self.assertEqual(result,{'video_id':'video'})
        self.assertEqual(saved[0][0],('private_locked',))
        self.assertEqual(request.calls[0][1]['headers']['Content-Range'],'bytes 0-2/3')
    def test_youtube_failed_write_not_retried(self):
        request=Mock([ok(status=500)])
        with self.assertRaises(RemoteError): YouTube(request).status('saved',10)
        self.assertEqual(len(request.calls),1)
    def test_drive_pagination_and_download(self):
        request=Mock([ok({'files':[{'id':'one'}],'nextPageToken':'next'}),ok({'files':[{'id':'two'}]}),ok(body=b'bytes')])
        drive=Drive(request)
        self.assertEqual([x['id'] for x in drive.list_queue('folder')],['one','two'])
        self.assertEqual(request.calls[1][1]['params']['pageToken'],'next')
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'clip'; drive.download('one',dest); self.assertEqual(dest.read_bytes(),b'bytes')
    def test_instagram_no_http_source(self):
        with self.assertRaises(ValueError): Instagram(Mock([]),'v25.0').create('u',{'caption':'c'},'http://bad',lambda *a,**k:None)
    def test_instagram_no_unreviewed_publish(self):
        request=Mock([])
        with self.assertRaises(ValueError): Instagram(request,'v25.0').publish('u','c',False,lambda *a,**k:None)
        self.assertFalse(request.calls)
    def test_instagram_waits_for_finished(self):
        request=Mock([ok({'status_code':'IN_PROGRESS'})])
        with self.assertRaises(RemoteError): Instagram(request,'v25.0').publish('u','c',True,lambda *a,**k:None)
        self.assertEqual(len(request.calls),1)
    def test_instagram_uncertain_before_publish(self):
        states=[]
        def request(method,url,**kwargs):
            if method=='GET': return ok({'status_code':'FINISHED'})
            self.assertEqual(states[-1],'uncertain')
            return ok({'id':'published'})
        result=Instagram(request,'v25.0').publish('u','c',True,lambda state,**k:states.append(state))
        self.assertEqual(states,['uncertain','published']); self.assertEqual(result,'published')
    def test_instagram_failed_publish_preserves_uncertainty(self):
        request=Mock([ok({'status_code':'FINISHED'}),ok(status=500)]); saved=[]
        with self.assertRaises(RemoteError): Instagram(request,'v25.0').publish('u','c',True,lambda state,**k:saved.append(state))
        self.assertEqual(saved,['uncertain']); self.assertEqual(len(request.calls),2)

if __name__=='__main__': unittest.main()
