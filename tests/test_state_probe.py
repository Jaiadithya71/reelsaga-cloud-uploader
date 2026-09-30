import unittest
from actions_state_probe import probe
from tests.test_durable_state import MemoryCAS
class ProbeTests(unittest.TestCase):
    def test_final_stopped(self):
        b=MemoryCAS(); result=probe(b,'one');self.assertTrue(result['stop_control_verified'])
        self.assertFalse(b.get('account-control')[0]['enabled'])
    def test_duplicate_refuses(self):
        b=MemoryCAS();probe(b,'one')
        with self.assertRaises(RuntimeError):probe(b,'one')
