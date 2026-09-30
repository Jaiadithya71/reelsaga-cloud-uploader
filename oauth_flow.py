"""PKCE/state helpers. Client type, callback and scopes must be reviewed first."""
import base64
import hashlib
import secrets
from urllib.parse import urlencode, urlsplit

class OAuthFlowError(RuntimeError):pass

class OAuthAttempt:
    def __init__(self, client_id, redirect_uri, scopes):
        if not client_id or not scopes:raise OAuthFlowError('Client and scopes required')
        p=urlsplit(redirect_uri)
        if p.fragment or p.username or p.password:raise OAuthFlowError('Invalid callback')
        if not (p.scheme=='https' or (p.scheme=='http' and p.hostname in ('127.0.0.1','::1'))):
            raise OAuthFlowError('HTTPS or approved desktop loopback callback required')
        self.client_id,self.redirect_uri,self.scopes=client_id,redirect_uri,tuple(scopes)
        self.verifier=secrets.token_urlsafe(64)
        self.state=secrets.token_urlsafe(32)
        self.used=False
    def authorization_url(self):
        challenge=base64.urlsafe_b64encode(hashlib.sha256(self.verifier.encode()).digest()).rstrip(b'=').decode()
        return 'https://accounts.google.com/o/oauth2/v2/auth?'+urlencode({
            'client_id':self.client_id,'redirect_uri':self.redirect_uri,
            'response_type':'code','scope':' '.join(self.scopes),'state':self.state,
            'code_challenge':challenge,'code_challenge_method':'S256','access_type':'offline'})
    def accept_callback(self, state, code, error=None):
        if self.used:raise OAuthFlowError('Authorization attempt already consumed')
        if not isinstance(state,str) or not secrets.compare_digest(state,self.state):
            raise OAuthFlowError('OAuth state mismatch')
        self.used=True
        if error or not code:raise OAuthFlowError('Authorization not completed')
        return {'client_id':self.client_id,'redirect_uri':self.redirect_uri,
                'grant_type':'authorization_code','code':code,'code_verifier':self.verifier}
