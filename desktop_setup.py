"""One-time Desktop OAuth bootstrap. Run on owner's PC, never in Actions.

Requires separately installed keyring with a native OS secure backend. Credentials
stay in OS keyring. No printing, plaintext export or automated GitHub transfer.
"""
import argparse
import json
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from oauth_flow import OAuthAttempt
from transport import GoogleTokenForms, Transport

SCOPES=('https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube.readonly')
CHANNEL='UC71kSXnAt6Ipy7KqVVo3mdA'
SERVICE='ReelSaga Upload Queue'
ACCOUNT='reelsaga-upload-queue'

class SetupError(RuntimeError):pass

def desktop_config(path):
    data=json.loads(Path(path).read_text())
    config=data.get('installed')
    if not config or not config.get('client_id') or not config.get('client_secret'):
        raise SetupError('A downloaded Desktop OAuth client JSON is required')
    return config

def secure_keyring():
    import keyring
    backend=keyring.get_keyring()
    module=type(backend).__module__
    if module not in ('keyring.backends.Windows','keyring.backends.macOS','keyring.backends.SecretService'):
        raise SetupError('Native OS secure keyring required; plaintext and fallback backends rejected')
    return keyring

def validate_tokens(data):
    if not data.get('refresh_token') or not data.get('access_token'):
        raise SetupError('Offline grant not issued; no credentials stored')
    if data.get('token_type','').lower()!='bearer' or not set(SCOPES)<=set(data.get('scope','').split()):
        raise SetupError('Required scopes were not granted; no credentials stored')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--client-json',required=True)
    args=parser.parse_args()
    config=desktop_config(args.client_json)
    keyring=secure_keyring()
    print('This setup requests YouTube upload and read-only channel/processing access.')
    print('No Drive grant. Sign in with the 71 account and select the ReelSaga channel.')
    if input('Continue with these permissions? Type YES: ').strip()!='YES':
        raise SetupError('Setup cancelled')
    result={}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            parsed=urlsplit(self.path)
            if parsed.path!='/callback':
                self.send_error(404);return
            params=parse_qs(parsed.query)
            try:
                payload=attempt.accept_callback(params.get('state',[None])[0],
                    params.get('code',[None])[0],params.get('error',[None])[0])
                result['payload']=payload
                text=b'Authorization received. Return to the setup program. No upload was performed.'
                self.send_response(200)
            except Exception:
                text=b'Authorization was not accepted. Return to the setup program.'
                self.send_response(400)
                if attempt.used:result['error']=True
            self.send_header('Content-Type','text/plain; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Length',str(len(text)))
            self.end_headers();self.wfile.write(text)
    with HTTPServer(('127.0.0.1',0),Handler) as server:
        server.timeout=1
        callback=f'http://127.0.0.1:{server.server_port}/callback'
        attempt=OAuthAttempt(config['client_id'],callback,SCOPES)
        if not webbrowser.open(attempt.authorization_url()):
            raise SetupError('Browser could not open; no credentials stored')
        deadline=time.monotonic()+300
        while not result and time.monotonic()<deadline:server.handle_request()
    if not result.get('payload'):raise SetupError('Authorization incomplete or timed out')
    payload=dict(result['payload'],client_secret=config['client_secret'])
    response=GoogleTokenForms()('https://oauth2.googleapis.com/token',payload)
    if response.status!=200:raise SetupError('Token exchange failed; no automatic retry')
    validate_tokens(response.data)
    api=Transport(lambda:response.data['access_token'],{'www.googleapis.com'})
    identity=api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'id,snippet','mine':'true'})
    ids={item.get('id') for item in identity.data.get('items',[])}
    if identity.status!=200 or ids!={CHANNEL}:
        raise SetupError('Destination channel mismatch; credentials not stored')
    record={'client_id':config['client_id'],'client_secret':config['client_secret'],
            'refresh_token':response.data['refresh_token'],
            'granted_scopes':response.data['scope'].split(),'channel_id':CHANNEL}
    keyring.set_password(SERVICE,ACCOUNT,json.dumps(record))
    print('ReelSaga channel verified. Credentials saved only in your OS keyring.')
    print('No video uploaded. Actions connection and audit remain separate steps.')

if __name__=='__main__':
    try:main()
    except Exception:
        print('Setup stopped. No secrets shown. Review account/client setup before trying again.')
        raise SystemExit(1)
