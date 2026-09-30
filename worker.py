"""One-item resumable worker with injected auth, APIs, and durable state.

No runtime backend is selected. This is never called by the preflight workflow.
"""
from pathlib import Path
from reelqueue import validate, verify_bytes

class NeedsReview(RuntimeError): pass

class Worker:
    def __init__(self, drive, youtube, instagram, ledger, resolve_media, check_identity):
        self.drive, self.youtube, self.instagram = drive,youtube,instagram
        self.ledger, self.resolve_media, self.check_identity = ledger,resolve_media,check_identity

    def run(self,item,platform,catalog,directory,canary_reviewed=False):
        validate(item,catalog,'UC71kSXnAt6Ipy7KqVVo3mdA','reelsaga3000')
        # Source identity verified every run. A stored username alone is not enough.
        self.check_identity(platform,item)
        state=self.ledger.resume(item['id'],platform)
        if state=='do_not_create': return state
        if state=='reconcile_manually': raise NeedsReview('Prior write uncertain; no new creation')
        checkpoint=lambda state,**k:self.ledger.checkpoint(item['id'],platform,state,**k)
        if platform=='instagram' and state=='unclaimed' and (canary_reviewed is not True or not item.get('instagram_user_id')):
            raise NeedsReview('Instagram canary/verified ID gate is closed')
        if state=='unclaimed':
            if not self.ledger.claim(item,platform):
                raise NeedsReview('Concurrent start')
            state='newly_claimed'
        record,_=self.ledger.backend.get(self.ledger.key(item['id'],platform))
        if platform=='instagram' and state=='read_saved_container':
            status=self.instagram.status(record['external_id'])
            return {'container_id':record['external_id'],'status':status,'action':'review_before_publish'}
        path=Path(directory)/'verified-upload.mp4'
        self.drive.download(item['drive_file_id'],path)
        verify_bytes(path,item['sha256'])
        if platform=='youtube':
            if state=='query_saved_upload_session':
                session=record['session']; status=self.youtube.status(session,path.stat().st_size)
                if 'video_id' in status:
                    checkpoint('private_locked',external_id=status['video_id']);return status
                offset=status['offset']
            else:
                session=self.youtube.start(item,path.stat().st_size,checkpoint);offset=0
            # Bounded chunk loop; interrupted runs resume from saved session.
            for _ in range(100):
                result=self.youtube.send_chunk(session,path,offset,checkpoint)
                if 'video_id' in result:return result
                if result['offset']<=offset:raise NeedsReview('Upload made no progress')
                offset=result['offset']
            raise NeedsReview('Chunk budget exceeded; resume saved session')
        if canary_reviewed is not True:
            raise NeedsReview('Instagram canary gate is closed')
        media_url=self.resolve_media(path,item)
        container=self.instagram.create(item['instagram_user_id'],item,media_url,checkpoint)
        return {'container_id':container,'action':'read_processing_status_later'}
