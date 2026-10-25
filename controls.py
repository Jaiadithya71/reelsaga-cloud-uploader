"""Fail-closed operator controls. Backend/tokens remain injected, not connected."""
class ControlError(RuntimeError):
    pass

class Controls:
    def __init__(self, backend, revoke):
        self.backend, self.revoke = backend, revoke

    def set_access(self, enabled, verified=False):
        if enabled and verified is not True:
            raise ControlError('Reviewed identity, scopes and policy required')
        record, version = self.backend.get('account-control')
        if not self.backend.compare_and_swap('account-control', version,
                                             {'enabled': bool(enabled)}):
            raise ControlError('Control update failed; stop writes')

    def require_enabled(self):
        record, _ = self.backend.get('account-control')
        if not record or record.get('enabled') is not True:
            raise ControlError('Account access disabled')

    def disconnect(self):
        # Stop work first. A revoke failure must never restore execution.
        self.set_access(False)
        self.revoke()
