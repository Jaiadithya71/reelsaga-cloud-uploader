import unittest
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('reelqueue',Path(__file__).parents[1]/'reelqueue.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.catalog={'blood':{'drama_url':'https://r.reelsgo.tv/FeeSIvFHqAog','app_url':'https://r.reelsgo.tv/yTQNUiohzlIp'}}
        self.item=dict(id='blood-ep1-p1',series_id='blood',episode=1,part=1,part_count=3,drive_file_id='test',sha256='a'*64,title='The Blood Pact Game - Episode 1 Part 1/3',description='',caption='',source_width=1080,source_height=1920,width=1080,height=1920,duration_seconds=37.625,whole_episode_parts_verified=True,pixels_verified=True,decode_verified=True,youtube_channel_id='UC71kSXnAt6Ipy7KqVVo3mdA',instagram_username='reelsaga3000',**self.catalog['blood'])
        text='Watch '+self.item['drama_url']+'\nGet the app '+self.item['app_url']+'\nAffiliate links: I may earn a commission if you use them.'
        self.item['description']=self.item['caption']=text
    def validate(self):q.validate(self.item,self.catalog,'UC71kSXnAt6Ipy7KqVVo3mdA','reelsaga3000')
    def test_valid(self):self.validate()
    def test_wrong_identity(self):
        self.item['instagram_username']='other'
        with self.assertRaises(q.ValidationError):self.validate()
    def test_no_downscale(self):
        self.item['width']=720
        with self.assertRaises(q.ValidationError):self.validate()
    def test_exact_links(self):
        self.item['app_url']+='?utm=x'
        with self.assertRaises(q.ValidationError):self.validate()
    def test_disclosure(self):
        self.item['caption']='No disclosure'
        with self.assertRaises(q.ValidationError):self.validate()
    def test_bio(self):
        self.item['caption']+=' link in bio'
        with self.assertRaises(q.ValidationError):self.validate()
    def test_duration(self):
        self.item['duration_seconds']=56
        with self.assertRaises(q.ValidationError):self.validate()
    def test_no_duplicate(self):
        ledger=q.Ledger(':memory:')
        self.assertTrue(ledger.begin(self.item,'youtube'))
        self.assertFalse(ledger.begin(self.item,'youtube'))
        ledger.record(self.item['id'],'youtube','uncertain',session='session-test')
        self.assertFalse(ledger.begin(self.item,'youtube'))
    def test_no_changed_metadata(self):
        ledger=q.Ledger(':memory:');ledger.begin(self.item,'instagram')
        self.item['caption']+=' changed'
        with self.assertRaises(q.ValidationError):ledger.begin(self.item,'instagram')
    def test_published_terminal(self):
        ledger=q.Ledger(':memory:');ledger.begin(self.item,'instagram');ledger.record(self.item['id'],'instagram','published','123')
        with self.assertRaises(q.ValidationError):ledger.record(self.item['id'],'instagram','uploading')
if __name__=='__main__':unittest.main()
