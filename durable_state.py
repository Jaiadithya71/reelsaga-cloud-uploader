"""Remote compare-and-swap checkpoints. Backend must supply real durable CAS.

Do not use Actions artifacts/caches as a transactional ledger. No backend is
connected here. Persist a claim before creating any platform resource.
"""
import hashlib
import json

class Conflict(RuntimeError):
    pass

class DurableLedger:
    def __init__(self, backend):
        self.backend = backend

    @staticmethod
    def key(item_id, platform):
        if platform not in ('youtube', 'instagram'):
            raise ValueError('Unknown platform')
        return hashlib.sha256((platform + ':' + item_id).encode()).hexdigest()

    def claim(self, item, platform):
        key = self.key(item['id'], platform)
        metadata_hash = hashlib.sha256(json.dumps(item, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        existing, version = self.backend.get(key)
        if existing:
            if existing['metadata_hash'] != metadata_hash:
                raise Conflict('Metadata changed after claim')
            return False
        record = {'id': item['id'], 'platform': platform, 'metadata_hash': metadata_hash, 'state': 'started', 'external_id': None, 'session': None}
        if not self.backend.compare_and_swap(key, version, record):
            raise Conflict('Concurrent claim; reread, never upload blindly')
        return True

    def checkpoint(self, item_id, platform, state, external_id=None, session=None):
        allowed = {'started','uploading','processing','private_locked','ready_for_review','published','blocked','uncertain'}
        if state not in allowed:
            raise ValueError('Unknown state')
        key = self.key(item_id, platform)
        record, version = self.backend.get(key)
        if not record:
            raise Conflict('Missing durable claim')
        if record['state'] == 'published' and state != 'published':
            raise Conflict('Published job cannot restart')
        record = dict(record, state=state)
        if external_id is not None:
            record['external_id'] = external_id
        if session is not None:
            record['session'] = session
        if not self.backend.compare_and_swap(key, version, record):
            raise Conflict('Checkpoint failed; stop external writes')

    def resume(self, item_id, platform):
        record, _ = self.backend.get(self.key(item_id, platform))
        if not record:
            return 'unclaimed'
        if record['state'] == 'uploading' and record['session']:
            return 'query_saved_upload_session'
        if record['state'] == 'processing' and record['external_id']:
            return 'read_saved_container'
        if record['state'] in ('published','private_locked','blocked','ready_for_review'):
            return 'do_not_create'
        # A claim alone cannot prove no external creation happened before a crash.
        return 'reconcile_manually'
