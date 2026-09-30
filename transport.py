"""Bounded HTTPS transport. Not wired to a workflow or real credentials.

Token injection and persistence are caller-owned. No automatic network retry.
Redirects are rejected so credentials cannot be forwarded to another origin.
"""
import json
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from adapters import Response, RemoteError

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class Transport:
    def __init__(self, token, hosts, opener=None, timeout=30):
        self.token, self.hosts = token, frozenset(hosts)
        self.opener = opener or build_opener(NoRedirect)
        self.timeout = timeout

    def __call__(self, method, url, params=None, json=None, body=None, headers=None):
        parts = urlsplit(url)
        if (parts.scheme != 'https' or parts.hostname not in self.hosts or
            parts.username or parts.password or parts.fragment or
            parts.port not in (None,443)):
            raise RemoteError('Unapproved API origin')
        if json is not None and body is not None:
            raise ValueError('Choose JSON or raw body')
        if method not in ('GET','POST','PUT'):
            raise ValueError('Unapproved HTTP method')
        if params:
            url += ('&' if parts.query else '?') + urlencode(params)
        outgoing = dict(headers or {})
        if any(k.lower()=='authorization' for k in outgoing):
            raise ValueError('Authorization is token-provider owned')
        if json is not None:
            body = globals()['json'].dumps(json).encode()
            outgoing['Content-Type']='application/json'
        token=self.token()
        if not isinstance(token,str) or not token or '\n' in token or '\r' in token:
            raise RemoteError('Credential unavailable')
        outgoing['Authorization']='Bearer '+token
        req=Request(url,data=body,headers=outgoing,method=method)
        try:
            result=self.opener.open(req,timeout=self.timeout)
        except HTTPError as exc:
            result=exc
        except Exception:
            # Network errors may contain secret-bearing session URLs.
            raise RemoteError('Network result uncertain; reconcile before retry') from None
        with result:
            raw=result.read()
            try:
                data=globals()['json'].loads(raw) if raw else {}
            except (ValueError,UnicodeDecodeError):
                data={}
            if not isinstance(data,dict):data={}
            return Response(result.code,data,dict(result.headers),raw)
