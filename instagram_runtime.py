"""Instagram own-account preflight and token lifecycle. Not live connected.

Default is OFF. No publishing, account conversion, app creation or token logging.
"""
import time
from adapters import checked

USERNAME='reelsaga3000'
SCOPES=frozenset({'instagram_business_basic','instagram_business_content_publish'})
class InstagramGateError(RuntimeError):pass

def validate_record(record):
    if record.get('username')!=USERNAME or not record.get('user_id'):
        raise InstagramGateError('Account binding missing')
    if not SCOPES<=set(record.get('granted_scopes',[])):
        raise InstagramGateError('Publishing scope missing')
    if not record.get('access_token') or record.get('expires_at',0)<=time.time():
        raise InstagramGateError('Token missing or expired')
    return record

def preflight(api,version,record,planned=1,conservative_cap=50):
    validate_record(record)
    if not version.startswith('v') or not 1<=planned<=conservative_cap<=50:
        raise InstagramGateError('Invalid bounded plan')
    base='https://graph.instagram.com/'+version
    identity=checked(api('GET',base+'/me',params={'fields':'user_id,username,account_type'})).data
    if identity.get('username')!=USERNAME or str(identity.get('user_id'))!=str(record['user_id']) or identity.get('account_type') not in ('BUSINESS','MEDIA_CREATOR','Business','Media_Creator'):
        raise InstagramGateError('Live account mismatch')
    limits=checked(api('GET',base+'/'+str(record['user_id'])+'/content_publishing_limit',params={'fields':'config,quota_usage'})).data.get('data',[])
    if len(limits)!=1:raise InstagramGateError('Live quota unavailable')
    limit=limits[0];usage=limit.get('quota_usage');live=limit.get('config',{}).get('quota_total')
    if not isinstance(usage,int) or not isinstance(live,int):raise InstagramGateError('Live quota incomplete')
    cap=min(live,conservative_cap)
    if usage+planned>cap:raise InstagramGateError('Plan exceeds rolling quota')
    return {'username':USERNAME,'user_id':str(record['user_id']),'account_type':identity['account_type'],'quota_usage':usage,'effective_cap':cap,'remaining':max(0,cap-usage),'planned':planned,'publishing_enabled':False}

class InstagramToken:
    def __init__(self,store,request,clock=time.time):self.store,self.request,self.clock=store,request,clock
    def refresh(self):
        record=self.store.read();validate_record(record);now=self.clock()
        if now-record.get('issued_at',now)<86400:
            raise InstagramGateError('Token must be at least24hours old')
        response=checked(self.request('GET','https://graph.instagram.com/refresh_access_token',params={'grant_type':'ig_refresh_token','access_token':record['access_token']})).data
        if not response.get('access_token') or not isinstance(response.get('expires_in'),int) or response['expires_in']<=0:
            raise InstagramGateError('Refresh result invalid')
        updated=dict(record,access_token=response['access_token'],issued_at=now,expires_at=now+response['expires_in'])
        self.store.write(updated)
        return {'refreshed':True,'expires_at':updated['expires_at']}
