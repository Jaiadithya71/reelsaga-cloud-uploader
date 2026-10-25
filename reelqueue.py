"""Fail-closed queue validation and durable, duplicate-resistant publishing ledger."""
from __future__ import annotations
import hashlib
import json
import sqlite3
from pathlib import Path

class ValidationError(ValueError):
    pass

def validate(item: dict, catalog: dict, target_channel: str, target_ig: str) -> None:
    required = {'id', 'series_id', 'episode', 'part', 'part_count', 'drive_file_id',
                'sha256', 'title', 'description', 'caption', 'source_width',
                'source_height', 'width', 'height', 'duration_seconds',
                'whole_episode_parts_verified', 'pixels_verified', 'decode_verified',
                'youtube_channel_id', 'instagram_username', 'drama_url', 'app_url'}
    missing = required - item.keys()
    if missing:
        raise ValidationError('Missing: ' + ', '.join(sorted(missing)))
    if item['youtube_channel_id'] != target_channel or item['instagram_username'] != target_ig:
        raise ValidationError('Wrong destination')
    if not all(item[k] is True for k in ('whole_episode_parts_verified', 'pixels_verified', 'decode_verified')):
        raise ValidationError('Quality verification incomplete')
    if (item['width'], item['height']) != (item['source_width'], item['source_height']):
        raise ValidationError('Source resolution changed')
    if not 0 < item['duration_seconds'] <= 55:
        raise ValidationError('Part exceeds approved duration')
    if not 1 <= item['part'] <= item['part_count']:
        raise ValidationError('Invalid part count')
    if len(item['sha256']) != 64 or any(c not in '0123456789abcdef' for c in item['sha256']):
        raise ValidationError('Invalid SHA256')
    issued = catalog.get(item['series_id'])
    if not issued or (item['drama_url'], item['app_url']) != (issued['drama_url'], issued['app_url']):
        raise ValidationError('Affiliate URLs must match issued title-specific URLs exactly')
    for field in ('description', 'caption'):
        if any(item[url] not in item[field] for url in ('drama_url', 'app_url')):
            raise ValidationError('Missing exact links in ' + field)
        if 'Affiliate links: I may earn a commission if you use them.' not in item[field]:
            raise ValidationError('Disclosure absent in ' + field)
    if len(item['title']) > 100 or len(item['description']) > 5000 or len(item['caption']) > 2200:
        raise ValidationError('Metadata too long')
    if 'link in bio' in item['caption'].lower() and not item.get('matching_bio_link_verified'):
        raise ValidationError('Bio destination not verified')

def verify_bytes(path: Path, expected: str) -> None:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    if h.hexdigest() != expected:
        raise ValidationError('Downloaded content hash mismatch')

class Ledger:
    """Storage must be persistent; a Render cron's ephemeral SQLite is not enough."""
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT, platform TEXT, state TEXT, metadata TEXT, external_id TEXT, session TEXT, PRIMARY KEY(id,platform))')
        self.db.commit()

    def begin(self, item: dict, platform: str) -> bool:
        if platform not in ('youtube', 'instagram'):
            raise ValidationError('Unknown platform')
        encoded = json.dumps(item, sort_keys=True, separators=(',', ':'))
        with self.db:
            row = self.db.execute('SELECT metadata FROM jobs WHERE id=? AND platform=?', (item['id'], platform)).fetchone()
            if row:
                if row[0] != encoded:
                    raise ValidationError('Queue item changed after start; owner review required')
                return False
            self.db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?)', (item['id'], platform, 'started', encoded, None, None))
        return True

    def record(self, id: str, platform: str, state: str, external_id: str | None = None, session: str | None = None):
        if state not in {'started', 'uploading', 'processing', 'private_locked', 'ready_for_review', 'published', 'blocked', 'uncertain'}:
            raise ValidationError('Unknown state')
        with self.db:
            current = self.db.execute('SELECT state FROM jobs WHERE id=? AND platform=?', (id, platform)).fetchone()
            if not current:
                raise ValidationError('Job not claimed')
            if current[0] == 'published' and state != 'published':
                raise ValidationError('Published item cannot be retried')
            self.db.execute('UPDATE jobs SET state=?, external_id=COALESCE(?,external_id), session=COALESCE(?,session) WHERE id=? AND platform=?', (state, external_id, session, id, platform))

    def state(self, id: str, platform: str):
        return self.db.execute('SELECT state,external_id,session FROM jobs WHERE id=? AND platform=?', (id, platform)).fetchone()
