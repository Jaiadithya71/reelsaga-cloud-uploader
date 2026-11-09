"""Live pre-flight for any ReelSaga public release: cross-lane 1-hour spacing.

Reads each lane's LAST ACTUAL PUBLIC post time from the provider, then applies
release_spacing.require_release (user rule 2026-11-01 22:16:22 IST: one post
per hour across both lanes, measured from each actual post). Fails closed:
any unreadable lane, identity mismatch or unmet spacing exits non-zero and
prints a JSON decision. Run before EVERY public flip or scheduled publish.
"""
import datetime
import json
import os
import sys

from actions_canary import Store
from desktop_setup import CHANNEL, SCOPES
from provision_actions import validated_record
from credentials import GoogleCredentials
from transport import Transport, GoogleTokenForms
from adapters import checked
from release_spacing import require_release

EXPECTED_IG_NAME = 'reelsaga3000'


def youtube_last_public(api):
    # channelId-scoped search returns public videos only: the last ACTUAL public post.
    r = checked(api('GET', 'https://www.googleapis.com/youtube/v3/search', params={
        'part': 'snippet', 'channelId': CHANNEL, 'order': 'date',
        'type': 'video', 'maxResults': 5})).data
    items = r.get('items', [])
    if not items:
        return None  # verified: no public videos on the channel
    newest = max(x['snippet']['publishedAt'] for x in items)
    return datetime.datetime.fromisoformat(newest.replace('Z', '+00:00'))


def instagram_read_token():
    import urllib.parse
    import urllib.request
    endpoint = os.environ.pop('REELSAGA_IG_READER_URL', '')
    key = os.environ.pop('REELSAGA_IG_READ_KEY', '')
    parsed = urllib.parse.urlsplit(endpoint)
    if parsed.scheme != 'https' or parsed.hostname != 'kathirvelan-boutique.vercel.app' \
            or parsed.path != '/api/instagram/reelsaga-reader' or parsed.port not in (None, 443) \
            or parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise RuntimeError('Invalid reader destination')
    if not key or len(key) < 32:
        raise RuntimeError('Reader credential missing')

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(NoRedirect).open
    req = urllib.request.Request(endpoint, headers={'Authorization': 'Bearer ' + key,
                                                    'Accept': 'application/json'})
    with opener(req, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError('Reader response unverified')
        raw = response.read(65537)
    if len(raw) > 65536:
        raise RuntimeError('Oversized reader response')
    record = json.loads(raw)
    if not record.get('access_token'):
        raise RuntimeError('Reader record unusable')
    return record


def instagram_last_public_graph(record):
    token = record['access_token']
    base = 'https://graph.instagram.com/v26.0'
    import urllib.parse
    import urllib.request

    def get(path, params):
        params = dict(params, access_token=token)
        url = base + path + '?' + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError('Instagram read failed')
            return json.loads(response.read(262145))

    identity = get('/me', {'fields': 'user_id,username'})
    if identity.get('username') != EXPECTED_IG_NAME:
        raise RuntimeError('Live Instagram identity mismatch')
    media = get('/' + str(identity['user_id']) + '/media',
                {'fields': 'timestamp', 'limit': 5}).get('data', [])
    if not media:
        return None  # verified: no public media on the account
    newest = max(x['timestamp'] for x in media)
    return datetime.datetime.fromisoformat(newest)


def main():
    record = validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS', ''))
    credential = GoogleCredentials(Store(record), GoogleTokenForms(), SCOPES)
    token = credential.access_token()
    api = Transport(lambda: token, {'www.googleapis.com'})
    yt_last = youtube_last_public(api)
    ig_last = instagram_last_public_graph(instagram_read_token())
    now = datetime.datetime.now(datetime.timezone.utc)
    decision = require_release(now, {'youtube': yt_last, 'instagram': ig_last})
    out = {
        'allowed': True,
        'checked_at': now.isoformat(),
        'youtube_last_public': yt_last.isoformat() if yt_last else None,
        'instagram_last_public': ig_last.isoformat() if ig_last else None,
        'newest_lane': decision['newest_lane'],
        'earliest': decision['earliest'].isoformat() if decision['earliest'] else None,
    }
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'allowed': False, 'error': str(e)}, sort_keys=True))
        sys.exit(1)
