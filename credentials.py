"""Google refresh/revoke lifecycle with injected secure store and form transport.

Not connected. No secrets or remote response payloads in errors/logs.
"""
import time

class CredentialError(RuntimeError):
    pass

class GoogleCredentials:
    def __init__(self, store, post_form, required_scopes, clock=time.time):
        self.store, self.post_form = store, post_form
        self.required = frozenset(required_scopes)
        self.clock = clock
        self.cached = None
        self.expires = 0
        self.disabled = False

    def access_token(self):
        if self.disabled:
            raise CredentialError('Account disabled; owner reauthorization required')
        if self.cached and self.clock() < self.expires - 60:
            return self.cached
        config = self.store.read()
        if not config or not {'client_id','client_secret','refresh_token','granted_scopes'} <= config.keys():
            raise CredentialError('Credentials incomplete')
        if not self.required <= set(config['granted_scopes']):
            raise CredentialError('Required scope grant missing')
        try:
            response = self.post_form('https://oauth2.googleapis.com/token', {
                'client_id':config['client_id'], 'client_secret':config['client_secret'],
                'refresh_token':config['refresh_token'], 'grant_type':'refresh_token'})
        except Exception:
            self.cached = None
            raise CredentialError('Refresh failed; no automatic retry') from None
        if response.status != 200:
            self.cached = None
            if response.data.get('error') == 'invalid_grant':
                self.disabled = True
            raise CredentialError('Refresh rejected; owner reauthorization may be required')
        data = response.data
        token = data.get('access_token')
        lifetime = data.get('expires_in')
        if (not isinstance(token,str) or not token or '\n' in token or '\r' in token or
            data.get('token_type','').lower() != 'bearer' or
            isinstance(lifetime,bool) or not isinstance(lifetime,(int,float)) or lifetime <= 60):
            raise CredentialError('Invalid refresh response')
        if 'scope' in data and not self.required <= set(data['scope'].split()):
            raise CredentialError('Refresh scope grant incomplete')
        self.cached, self.expires = token, self.clock()+lifetime
        return self.cached

    def revoke(self):
        self.disabled = True
        self.cached = None
        config = self.store.read()
        if not config or not config.get('refresh_token'):
            raise CredentialError('Revocation requires stored token')
        try:
            response = self.post_form('https://oauth2.googleapis.com/revoke',
                                      {'token':config['refresh_token']})
        except Exception:
            raise CredentialError('Revocation uncertain; account remains disabled') from None
        if response.status != 200:
            raise CredentialError('Revocation not confirmed; account remains disabled')
        self.store.delete()
