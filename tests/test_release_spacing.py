import datetime
import unittest

from release_spacing import (LANES, MIN_PUBLIC_SPACING, SpacingError,
                             evaluate, require_release)

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 11, 9, 12, 0, tzinfo=UTC)


class ReleaseSpacingTest(unittest.TestCase):
    def test_rule_is_one_hour(self):
        self.assertEqual(MIN_PUBLIC_SPACING, datetime.timedelta(hours=1))
        self.assertEqual(set(LANES), {'youtube', 'instagram'})

    def test_no_public_posts_anywhere_allows_first_release(self):
        d = evaluate(NOW, {'youtube': None, 'instagram': None})
        self.assertTrue(d['allowed'])
        self.assertIsNone(d['earliest'])

    def test_exactly_one_hour_allows(self):
        last = NOW - datetime.timedelta(hours=1)
        d = evaluate(NOW, {'youtube': last, 'instagram': None})
        self.assertTrue(d['allowed'])
        self.assertEqual(d['earliest'], NOW)
        self.assertEqual(d['newest_lane'], 'youtube')

    def test_59_minutes_blocks(self):
        last = NOW - datetime.timedelta(minutes=59)
        d = evaluate(NOW, {'youtube': last, 'instagram': None})
        self.assertFalse(d['allowed'])
        self.assertEqual(d['earliest'], last + datetime.timedelta(hours=1))
        with self.assertRaises(SpacingError):
            require_release(NOW, {'youtube': last, 'instagram': None})

    def test_newest_post_on_other_lane_governs(self):
        yt = NOW - datetime.timedelta(hours=3)
        ig = NOW - datetime.timedelta(minutes=20)
        d = evaluate(NOW, {'youtube': yt, 'instagram': ig})
        self.assertFalse(d['allowed'])
        self.assertEqual(d['newest_lane'], 'instagram')
        self.assertEqual(d['earliest'], ig + datetime.timedelta(hours=1))

    def test_unknown_lane_fails_closed(self):
        with self.assertRaises(SpacingError):
            evaluate(NOW, {'youtube': NOW - datetime.timedelta(hours=5)})
        with self.assertRaises(SpacingError):
            evaluate(NOW, {})

    def test_naive_or_future_timestamps_fail_closed(self):
        naive = datetime.datetime(2026, 11, 9, 10, 0)
        with self.assertRaises(SpacingError):
            evaluate(NOW, {'youtube': naive, 'instagram': None})
        with self.assertRaises(SpacingError):
            evaluate(naive, {'youtube': None, 'instagram': None})
        with self.assertRaises(SpacingError):
            evaluate(NOW, {'youtube': NOW + datetime.timedelta(minutes=1),
                           'instagram': None})

    def test_restart_breach_would_have_been_blocked(self):
        # E1P1 public 02:02 IST; E1P2 flipped 02:34 IST (+32min) on 2026-11-09.
        ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        e1p1 = datetime.datetime(2026, 11, 9, 2, 2, tzinfo=ist)
        attempted = datetime.datetime(2026, 11, 9, 2, 34, tzinfo=ist)
        ig_last = datetime.datetime(2026, 11, 8, 12, 0, tzinfo=ist)
        d = evaluate(attempted, {'youtube': e1p1, 'instagram': ig_last})
        self.assertFalse(d['allowed'])
        self.assertEqual(d['earliest'], datetime.datetime(2026, 11, 9, 3, 2, tzinfo=ist))


if __name__ == '__main__':
    unittest.main()
