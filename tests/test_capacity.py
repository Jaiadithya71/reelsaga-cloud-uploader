import unittest
from capacity import plan,CapacityError
class CapacityTests(unittest.TestCase):
    def test_youtube_headroom(self):
        p=plan('youtube',100);self.assertEqual(p['max_new_attempts'],90);self.assertFalse(p['active']);self.assertEqual(p['spacing_seconds'],960)
    def test_instagram_live_smaller(self):self.assertEqual(plan('instagram',40)['max_new_attempts'],40)
    def test_attempts_count(self):self.assertEqual(plan('youtube',100,95,2)['max_new_attempts'],3)
    def test_zero_limit_blocks(self):
        with self.assertRaises(CapacityError):plan('instagram',0)
