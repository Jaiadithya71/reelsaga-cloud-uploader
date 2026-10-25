"""One owner-requested read-only verification. Never uploads or logs credentials."""
import json
import os
from desktop_setup import CHANNEL, SCOPES
from provision_actions import validated_record
from transport import GoogleTokenForms, Transport

class VerificationError(RuntimeError):
    pass

def verify(raw, forms=None, api_factory=None):
    record=validated_record(raw)
    forms=forms or GoogleTokenForms()
    response=forms('https://oauth2.googleapis.com/token', {
        'client_id':record['client_id'], 'client_secret':record['client_secret'],
        'refresh_token':record['refresh_token'], 'grant_type':'refresh_token'})
    data=response.data
    if response.status!=200 or not data.get('access_token') or data.get('token_type','').lower()!='bearer':
        raise VerificationError('Refresh verification failed; stopped without retry')
    # Stored scopes alone do not establish current scope. Missing live scope fails closed.
    if not set(SCOPES)<=set(data.get('scope','').split()):
        raise VerificationError('Live refresh response did not confirm both required scopes')
    api=(api_factory or (lambda token:Transport(lambda:token, {'www.googleapis.com'})))(data['access_token'])
    result=api('GET','https://www.googleapis.com/youtube/v3/channels',
               params={'part':'id,snippet','mine':'true'})
    if result.status!=200 or {x.get('id') for x in result.data.get('items',[])}!={CHANNEL}:
        raise VerificationError('Live channel identity mismatch; stopped')
    return {'channel_id':CHANNEL,'upload_scope_verified':True,'readonly_scope_verified':True,
            'private_canary_uploaded':False,'publishing_enabled':False}

def main():
    raw=os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS','')
    try:
        print(json.dumps(verify(raw),sort_keys=True))
    except Exception:
        print('Read-only verification failed. No video uploaded; no automatic retry; credentials not shown.')
        raise SystemExit(1) from None
if __name__=='__main__':main()
