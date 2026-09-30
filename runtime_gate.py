"""Explicit activation checks. No workflow entrypoint calls this yet."""
class ActivationError(RuntimeError):pass

REQUIRED = ('owner_scope_verified','identity_verified','remote_cas_live_tested',
            'secure_credentials_wired','control_stop_live_tested',
            'privacy_practices_reviewed','canary_saved_verified')

def require_activation(evidence, platform):
    if platform not in ('youtube','instagram'):
        raise ActivationError('Unknown platform')
    missing=[key for key in REQUIRED if evidence.get(key) is not True]
    if platform=='instagram' and evidence.get('https_media_relay_verified') is not True:
        missing.append('https_media_relay_verified')
    if missing:
        raise ActivationError('Activation blocked: '+', '.join(missing))
    return 'private_only' if platform=='youtube' and evidence.get('youtube_audit_passed') is not True else 'scoped_publishing'
