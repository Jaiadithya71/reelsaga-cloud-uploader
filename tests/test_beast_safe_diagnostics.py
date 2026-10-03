import contextlib,io,unittest
from unittest.mock import patch
import actions_beast_part as beast

class SafeDiagnostics(unittest.TestCase):
    def test_failure_stage_does_not_print_exception_or_secrets(self):
        with patch.object(beast,'validate',side_effect=RuntimeError('secret sentinel token')), contextlib.redirect_stdout(io.StringIO()) as out:
            with self.assertRaises(SystemExit): beast.main()
        text=out.getvalue()
        self.assertIn('Safe failure stage: manifest',text)
        self.assertNotIn('secret sentinel',text)
        self.assertNotIn('token',text)

    def test_scope_and_guard_kept(self):
        import inspect
        text=inspect.getsource(beast.run)
        self.assertIn("ledger.resume(item['id'],'youtube')!='unclaimed'",text)
        self.assertIn('controls.require_enabled()',text)
        self.assertIn("row['status']['privacyStatus']!='private'",text)
