"""Injectable API adapters. No credentials, implicit retry, or auto-publish."""
from dataclasses import dataclass
from pathlib import Path
import json
from urllib.parse import quote

class RemoteError(RuntimeError):
    pass

@dataclass
class Response:
    status: int
    data: dict
    headers: dict
    body: bytes = b''


def checked(response, allowed=(200, 201)):
    if response.status not in allowed:
        # Do not include response content, URLs, or tokens in logs.
        raise RemoteError(f'Remote operation failed with HTTP {response.status}; reconcile before retry')
    return response

class Drive:
    def __init__(self, request):
        self.request = request

    def list_queue(self, folder):
        if not folder or "'" in folder:
            raise ValueError('Invalid folder ID')
        rows, token = [], None
        while True:
            params = {'q': f"'{folder}' in parents and trashed=false", 'fields': 'nextPageToken,files(id,name,mimeType,size,md5Checksum)', 'pageSize': 100}
            if token:
                params['pageToken'] = token
            response = checked(self.request('GET', 'https://www.googleapis.com/drive/v3/files', params=params))
            rows.extend(response.data.get('files', []))
            token = response.data.get('nextPageToken')
            if not token:
                return rows

    def download(self, file_id, destination):
        response = checked(self.request('GET', 'https://www.googleapis.com/drive/v3/files/' + quote(file_id, safe=''), params={'alt': 'media'}))
        Path(destination).write_bytes(response.body)

class YouTube:
    """Uploads are forced Private. Saved resumable sessions must precede bytes."""
    def __init__(self, request):
        self.request = request

    def start(self, item, size, checkpoint):
        metadata = {'snippet': {'title': item['title'], 'description': item['description'], 'categoryId': '24'}, 'status': {'privacyStatus': 'private', 'selfDeclaredMadeForKids': False}}
        result = checked(self.request('POST', 'https://www.googleapis.com/upload/youtube/v3/videos', params={'uploadType': 'resumable', 'part': 'snippet,status'}, json=metadata, headers={'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(size)}))
        session = result.headers.get('Location') or result.headers.get('location')
        if not session or not session.startswith('https://www.googleapis.com/'):
            raise RemoteError('Unexpected resumable session location')
        checkpoint('uploading', session=session)
        return session

    def status(self, session, size):
        result = self.request('PUT', session, body=b'', headers={'Content-Length': '0', 'Content-Range': f'bytes */{size}'})
        checked(result, (200, 201, 308))
        if result.status == 308:
            value = result.headers.get('Range') or result.headers.get('range')
            return {'offset': int(value.rsplit('-', 1)[1]) + 1 if value else 0}
        return {'video_id': result.data['id']}

    def send_chunk(self, session, path, offset, checkpoint, chunk_size=8*1024*1024):
        if chunk_size <= 0 or chunk_size % (256*1024):
            raise ValueError('Chunk size must be a positive multiple of 256 KiB')
        size = Path(path).stat().st_size
        if not 0 <= offset < size:
            raise ValueError('Invalid offset')
        with open(path, 'rb') as source:
            source.seek(offset)
            content = source.read(chunk_size)
        result = checked(self.request('PUT', session, body=content, headers={'Content-Type': 'video/mp4', 'Content-Length': str(len(content)), 'Content-Range': f'bytes {offset}-{offset+len(content)-1}/{size}'}), (200, 201, 308))
        if result.status == 308:
            value = result.headers.get('Range') or result.headers.get('range')
            if not value:
                raise RemoteError('Server offset unknown; query saved session')
            return {'offset': int(value.rsplit('-', 1)[1])+1}
        video_id = result.data.get('id')
        if not video_id:
            raise RemoteError('Upload completion ID missing; reconcile saved session')
        checkpoint('private_locked', external_id=video_id)
        return {'video_id': video_id}

class Instagram:
    def __init__(self, request, api_version):
        if not api_version.startswith('v'):
            raise ValueError('Explicit supported API version required')
        self.request, self.base = request, f'https://graph.instagram.com/{api_version}'

    def identity(self):
        return checked(self.request('GET', self.base + '/me', params={'fields': 'user_id,username,account_type'})).data

    def create(self, user_id, item, media_url, checkpoint):
        if not media_url.startswith('https://'):
            raise ValueError('Instagram requires HTTPS hosted media')
        result = checked(self.request('POST', self.base + '/' + quote(user_id, safe='') + '/media', json={'media_type': 'REELS', 'video_url': media_url, 'caption': item['caption'], 'share_to_feed': True}))
        container = result.data['id']
        checkpoint('processing', external_id=container)
        return container

    def status(self, container):
        return checked(self.request('GET', self.base + '/' + quote(container, safe=''), params={'fields': 'status_code,status'})).data

    def publish(self, user_id, container, reviewed, checkpoint):
        if reviewed is not True:
            raise ValueError('Canary and owner publishing scope not verified')
        if self.status(container).get('status_code') != 'FINISHED':
            raise RemoteError('Container is not finished')
        # Persist uncertainty BEFORE a non-idempotent call. Never recreate on timeout.
        checkpoint('uncertain', external_id=container)
        result = checked(self.request('POST', self.base + '/' + quote(user_id, safe='') + '/media_publish', json={'creation_id': container}))
        media_id = result.data['id']
        checkpoint('published', external_id=media_id)
        return media_id
