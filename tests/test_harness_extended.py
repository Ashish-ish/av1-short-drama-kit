"""
Extended Unit & Edge-Case Tests for Transcoding Pipeline & Benchmark Harness.
Generated according to unit-testing-test-generate guidelines.
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from harness.config import (
    RUNGS,
    CODEC_STRINGS,
    MAX_PAPR_THRESHOLD,
    MIN_AV1_SAVING_THRESHOLD_PCT,
    RungConfig,
)
from harness.bd_rate import (
    polyfit_1d,
    polyval,
    polyint_definite,
    calculate_bd_rate,
    calculate_bd_vmaf,
)
from harness.vmaf import estimate_calibrated_vmaf
from harness.encode import (
    build_ffmpeg_encode_cmd,
    measure_cmaf_segments,
    generate_master_playlist,
    RenditionResult,
    synthesize_cmaf_rendition,
)
from harness.savings_calculator import (
    calculate_savings,
    calculate_data_per_minute,
)


class TestBdRateEdgeCases(unittest.TestCase):

    def test_polyfit_empty_or_mismatched(self):
        with self.assertRaises(ValueError):
            polyfit_1d([1.0], [1.0, 2.0])

    def test_polyfit_degree_fallback(self):
        # 2 points cannot fit cubic, should fallback to linear
        x = [1.0, 2.0]
        y = [3.0, 5.0]
        coeffs = polyfit_1d(x, y, degree=3)
        self.assertEqual(len(coeffs), 2)
        self.assertAlmostEqual(coeffs[0], 1.0, places=3)
        self.assertAlmostEqual(coeffs[1], 2.0, places=3)

    def test_polyint_definite(self):
        # Integral of 3x^2 from 0 to 2 is [x^3]_0^2 = 8
        coeffs = [0.0, 0.0, 3.0]
        res = polyint_definite(coeffs, 0.0, 2.0)
        self.assertAlmostEqual(res, 8.0, places=4)

    def test_bd_rate_insufficient_points(self):
        self.assertIsNone(calculate_bd_rate([100.0], [80.0], [50.0, 100.0], [80.0, 90.0]))

    def test_bd_rate_identical_curves(self):
        # Identical rate-distortion curves should yield 0.0% BD-rate
        r = [200.0, 400.0, 800.0, 1600.0]
        v = [75.0, 85.0, 92.0, 96.0]
        bd_rate = calculate_bd_rate(r, v, r, v)
        self.assertIsNotNone(bd_rate)
        self.assertAlmostEqual(bd_rate, 0.0, places=1)


class TestVmafModelEdgeCases(unittest.TestCase):

    def test_vmaf_bounds(self):
        # Extreme low bitrate should not drop below 20.0
        v_low = estimate_calibrated_vmaf("h264", 540, 960, 5.0, "talking_head")
        self.assertGreaterEqual(v_low, 20.0)

        # Extreme high bitrate should not exceed 98.5
        v_high = estimate_calibrated_vmaf("av1", 540, 960, 50000.0, "talking_head")
        self.assertLessEqual(v_high, 98.5)

    def test_complexity_hierarchy(self):
        # High motion should score lower VMAF than talking head at equal bitrate
        v_talking = estimate_calibrated_vmaf("h264", 540, 960, 700.0, "talking_head")
        v_motion = estimate_calibrated_vmaf("h264", 540, 960, 700.0, "high_motion")
        self.assertGreater(v_talking, v_motion)


class TestEncodeAndPaprVerification(unittest.TestCase):

    def test_papr_spike_detection(self):
        # Create a mock playlist with a 3x peak spike to verify failure detection
        tmp_dir = "/tmp/test_papr_spike"
        os.makedirs(tmp_dir, exist_ok=True)
        m3u8_path = os.path.join(tmp_dir, "index.m3u8")

        # Create segments: 3 small, 1 huge spike
        with open(os.path.join(tmp_dir, "seg_0.m4s"), "wb") as f:
            f.write(b"0" * 10000)
        with open(os.path.join(tmp_dir, "seg_1.m4s"), "wb") as f:
            f.write(b"0" * 10000)
        with open(os.path.join(tmp_dir, "seg_2.m4s"), "wb") as f:
            f.write(b"0" * 50000)  # 5x spike!

        with open(m3u8_path, "w") as f:
            f.write("#EXTM3U\n#EXTINF:2.0,\nseg_0.m4s\n#EXTINF:2.0,\nseg_1.m4s\n#EXTINF:2.0,\nseg_2.m4s\n#EXT-X-ENDLIST\n")

        avg_kbps, peak_kbps, papr, count = measure_cmaf_segments(m3u8_path)
        self.assertEqual(count, 3)
        self.assertGreater(papr, MAX_PAPR_THRESHOLD, "Spike segment should exceed 1.8 PAPR threshold")


class TestSavingsCalculatorEdgeCases(unittest.TestCase):

    def test_zero_egress_handling(self):
        res = calculate_savings(cdn_price_per_gb=0.015, monthly_egress_tb=0.0, monthly_viewing_minutes=0.0)
        self.assertIsNotNone(res)
        self.assertGreater(res["inputs"]["monthly_viewing_minutes"], 0)

    def test_extreme_market_price(self):
        # High-cost enterprise CDN ($0.08 / GB)
        res = calculate_savings(cdn_price_per_gb=0.08, monthly_egress_tb=500.0, av1_saving_pct=50.0)
        self.assertGreater(res["monthly_totals"]["gross_cdn_saved_usd"], 5000.0)


if __name__ == "__main__":
    unittest.main()
