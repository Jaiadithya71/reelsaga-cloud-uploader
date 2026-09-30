import unittest,time
from unittest.mock import Mock
from instagram_runtime import preflight,validate_record,InstagramGateError,InstagramToken,SCOPES
from adapters import Response
class InstagramRuntimeTests(unittest.TestCase):
    def record(self):return {'username':'reelsaga3000','user_id':'123','access_token':'mock','granted_scopes':list(SCOPES),'expires_at':time.time()+100000,'issued_at':time.time()-90000}
    def api(self,usage=0,total=100):return Mock(side_effect=[Response(200,{'user_id':'123','username':'reelsaga3000','account_type':'MEDIA_CREATOR'},{}),Response(200,{'data':[{'quota_usage':usage,'config':{'quota_total':total}}]}, {})])
    def test_bounded(self):
        r=preflight(self.api(),'v25.0',self.record(),39);self.assertEqual(r['effective_cap'],50);self.assertFalse(r['publishing_enabled'])
    def test_live_smaller_cap(self):self.assertEqual(preflight(self.api(total=40),'v25.0',self.record(),39)['effective_cap'],40)
    def test_used_quota_blocks(self):
        with self.assertRaises(InstagramGateError):preflight(self.api(usage=12),'v25.0',self.record(),39)
    def test_wrong_owner(self):
        with self.assertRaises(InstagramGateError):validate_record(dict(self.record(),username='other'))
    def test_missing_scope(self):
        with self.assertRaises(InstagramGateError):validate_record(dict(self.record(),granted_scopes=['instagram_business_basic']))
    def test_no_quota(self):
        api=Mock(side_effect=[Response(200,{'user_id':'123','username':'reelsaga3000','account_type':'MEDIA_CREATOR'},{}),Response(200,{'data':[]},{})])
        with self.assertRaises(InstagramGateError):preflight(api,'v25.0',self.record())
    def test_refresh(self):
        store=Mock();store.read.return_value=self.record();req=Mock(return_value=Response(200,{'access_token':'newmock','expires_in':5184000},{}))
        self.assertTrue(InstagramToken(store,req).refresh()['refreshed']);store.write.assert_called_once()
    def test_young_no_refresh(self):
        store=Mock();store.read.return_value=dict(self.record(),issued_at=time.time());req=Mock()
        with self.assertRaises(InstagramGateError):InstagramToken(store,req).refresh()
        req.assert_not_called()
