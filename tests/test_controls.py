import unittest
from unittest.mock import Mock
from controls import Controls, ControlError
from test_durable_state import MemoryCAS

class ControlTests(unittest.TestCase):
    def test_off_by_default(self):
        with self.assertRaises(ControlError):Controls(MemoryCAS(),Mock()).require_enabled()
    def test_enable_requires_review(self):
        with self.assertRaises(ControlError):Controls(MemoryCAS(),Mock()).set_access(True)
    def test_disconnect_stops_before_revoke(self):
        b=MemoryCAS(); c=Controls(b,Mock()); c.set_access(True,verified=True)
        c.disconnect()
        with self.assertRaises(ControlError):c.require_enabled()
        c.revoke.assert_called_once()
    def test_failed_revoke_remains_disabled(self):
        c=Controls(MemoryCAS(),Mock(side_effect=RuntimeError('offline')))
        c.set_access(True,verified=True)
        with self.assertRaises(RuntimeError):c.disconnect()
        with self.assertRaises(ControlError):c.require_enabled()
    def test_failed_control_cas_does_not_revoke(self):
        b=MemoryCAS();b.fail=True;c=Controls(b,Mock())
        with self.assertRaises(ControlError):c.disconnect()
        c.revoke.assert_not_called()
