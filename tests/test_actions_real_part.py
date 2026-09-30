import unittest,json,tempfile
from pathlib import Path
from unittest.mock import patch
from actions_real_part import validate,run
from tests.test_durable_state import MemoryCAS
from controls import Controls
from adapters import Response
from desktop_setup import CHANNEL

class RealPartTests(unittest.TestCase):
    def setUp(self):
        self.item=json.loads(Path('hybrid-test/ep4-part1.json').read_text())
        self.path='hybrid-test/ep4-part1.mp4'
    def test_manifest(self):validate(self.item,self.path)
    def test_ep6_bounded_manifests(self):
        for p in range(1,4):
            validate(json.loads(Path(f"hybrid-test/ep6-part{p}.json").read_text()),f"hybrid-test/ep6-part{p}.mp4")
    def test_hash_mismatch(self):
        item=dict(self.item,sha256='0'*64)
        with self.assertRaises(RuntimeError):validate(item,self.path)
    def test_wrong_item(self):
        with self.assertRaises(RuntimeError):validate(dict(self.item,id='other'),self.path)
    def test_missing_disclosure(self):
        with self.assertRaises(RuntimeError):validate(dict(self.item,description='missing'),self.path)
    def test_upload_chunks_and_rerun_block(self):
        backend=MemoryCAS();Controls(backend,lambda:None).set_access(True,verified=True);calls=[]
        def api(method,url,**kw):
            calls.append((method,url,kw))
            if method=='POST':
                self.assertEqual(kw['json']['status']['privacyStatus'],'private')
                return Response(200,{}, {'Location':'https://www.googleapis.com/upload/session'})
            if method=='PUT':
                content=kw['headers']['Content-Range']
                end=int(content.split('-')[1].split('/')[0])
                if end+1<self.item['bytes']:return Response(308,{}, {'Range':f'bytes=0-{end}'})
                return Response(200,{'id':'test-id'}, {})
            return Response(200,{'items':[{'snippet':{'channelId':CHANNEL,'title':self.item['title'],'description':self.item['description']},'status':{'privacyStatus':'private','selfDeclaredMadeForKids':False},'processingDetails':{'processingStatus':'processing'}}]}, {})
        result=run(backend,api,self.item,self.path)
        self.assertEqual(result['video_id'],'test-id');self.assertFalse(result['claims_verified'])
        self.assertEqual(len([c for c in calls if c[0]=='PUT']),2)
        before=len(calls)
        with self.assertRaises(RuntimeError):run(backend,api,self.item,self.path)
        self.assertEqual(len(calls),before)
    def test_disabled_blocks(self):
        with self.assertRaises(Exception):run(MemoryCAS(),lambda *a,**k:None,self.item,self.path)
