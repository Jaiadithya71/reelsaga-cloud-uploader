import unittest
from runtime_gate import require_activation, REQUIRED, ActivationError
class GateTests(unittest.TestCase):
    def test_default_closed(self):
        with self.assertRaises(ActivationError):require_activation({},'youtube')
    def test_each_missing_blocks(self):
        for key in REQUIRED:
            e=dict.fromkeys(REQUIRED,True);e[key]=False
            with self.assertRaises(ActivationError):require_activation(e,'youtube')
    def test_youtube_private_until_audit(self):
        self.assertEqual(require_activation(dict.fromkeys(REQUIRED,True),'youtube'),'private_only')
    def test_youtube_audit_does_not_replace_controls(self):
        with self.assertRaises(ActivationError):require_activation({'youtube_audit_passed':True},'youtube')
    def test_instagram_relay_required(self):
        with self.assertRaises(ActivationError):require_activation(dict.fromkeys(REQUIRED,True),'instagram')
    def test_boolean_not_truthy(self):
        with self.assertRaises(ActivationError):require_activation(dict.fromkeys(REQUIRED,'yes'),'youtube')
