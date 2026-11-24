"""
Unit and Integration Tests for AV1 Adoption Kit Transcoding Pipeline & Benchmark Harness.
Verifies BD-rate calculations, FFmpeg command generation, VBV/mbr capping,
PAPR verification, master playlist structure, and savings arithmetic.
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
)
from harness.bd_rate import (
    polyfit_1d,
    polyval,
    calculate_bd_rate,
    calculate_bd_vmaf,
)
from harness.encode import (
    build_ffmpeg_encode_cmd,
    generate_master_playlist,
    RenditionResult,
    synthesize_cmaf_rendition,
)
from harness.vmaf import estimate_calibrated_vmaf
from harness.vmaf_bd_rate import evaluate_rung_for_clip
from harness.savings_calculator import calculate_savings, calculate_data_per_minute


class TestBdRateCalculation(unittest.TestCase):

    def test_polynomial_fitting(self):
        # Test fitting y = 2 + 3x + x^2
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0 + 3.0 * xi + xi ** 2 for xi in x]
        coeffs = polyfit_1d(x, y, degree=2)
        self.assertAlmostEqual(coeffs[0], 2.0, places=3)
        self.assertAlmostEqual(coeffs[1], 3.0, places=3)
        self.assertAlmostEqual(coeffs[2], 1.0, places=3)

    def test_bd_rate_saving_calculation(self):
        # Reference H.264
        r_ref = [350.0, 700.0, 1200.0, 2000.0]
        v_ref = [80.0, 88.0, 93.0, 96.0]

        # Test AV1: requiring ~50% bitrate for identical quality
        r_av1 = [175.0, 350.0, 600.0, 1000.0]
        v_av1 = [80.5, 88.5, 93.2, 96.1]

        bd_rate = calculate_bd_rate(r_ref, v_ref, r_av1, v_av1)
        self.assertIsNotNone(bd_rate)
        # Should be roughly -52%
        self.assertTrue(-55.0 <= bd_rate <= -45.0, f"Expected ~-50% saving, got {bd_rate}")

        bd_vmaf = calculate_bd_vmaf(r_ref, v_ref, r_av1, v_av1)
        self.assertIsNotNone(bd_vmaf)
        self.assertTrue(bd_vmaf > 0, "Test codec should exhibit positive BD-VMAF gain at equal bitrate")


class TestEncodePipeline(unittest.TestCase):

    def test_ffmpeg_cmd_structure_adr001(self):
        rung = RUNGS["540p"]

        # H.264 command check (VBV maxrate and bufsize)
        cmd_h264 = build_ffmpeg_encode_cmd("master.mp4", "out.mp4", "h264", rung, crf=23, maxrate_kbps=700)
        cmd_str_h264 = " ".join(cmd_h264)
        self.assertIn("-c:v libx264", cmd_str_h264)
        self.assertIn("-maxrate 700k", cmd_str_h264)
        self.assertIn("-bufsize 1400k", cmd_str_h264)
        self.assertIn("-sc_threshold 0", cmd_str_h264)
        self.assertIn("-g 60 -keyint_min 60", cmd_str_h264)

        # HEVC command check
        cmd_hevc = build_ffmpeg_encode_cmd("master.mp4", "out.mp4", "hevc", rung, crf=25, maxrate_kbps=400)
        cmd_str_hevc = " ".join(cmd_hevc)
        self.assertIn("-c:v libx265", cmd_str_hevc)
        self.assertIn("vbv-maxrate=400", cmd_str_hevc)
        self.assertIn("vbv-bufsize=800", cmd_str_hevc)
        self.assertIn("no-scenecut=1", cmd_str_hevc)

        # SVT-AV1 command check (mbr and fast-decode, NOT buf-sz)
        cmd_av1 = build_ffmpeg_encode_cmd("master.mp4", "out.mp4", "av1", rung, crf=35, maxrate_kbps=350)
        cmd_str_av1 = " ".join(cmd_av1)
        self.assertIn("-c:v libsvtav1", cmd_str_av1)
        self.assertIn("tune=0", cmd_str_av1)
        self.assertIn("fast-decode=1", cmd_str_av1)
        self.assertIn("scd=0", cmd_str_av1)
        self.assertIn("mbr=350", cmd_str_av1)
        self.assertNotIn("buf-sz", cmd_str_av1, "buf-sz must NOT be used for CRF mode in SVT-AV1")

    def test_papr_segment_measurement(self):
        rung = RUNGS["540p"]
        tmp_dir = "/tmp/test_cmaf_papr"
        res = synthesize_cmaf_rendition(tmp_dir, "av1", rung, duration_sec=6.0)

        self.assertTrue(os.path.exists(res.media_playlist_path))
        self.assertTrue(res.papr > 1.0, "PAPR should be > 1.0")
        self.assertTrue(res.papr <= MAX_PAPR_THRESHOLD, f"PAPR {res.papr} exceeded threshold {MAX_PAPR_THRESHOLD}")
        self.assertTrue(res.passed_papr_check)


class TestMasterPlaylistGeneration(unittest.TestCase):

    def test_master_playlist_tags_and_codecs(self):
        renditions = [
            RenditionResult("av1", "360p", 360, 640, 175.0, 220.0, 1.25, 82.0, True, "av1/360p/index.m3u8", 3),
            RenditionResult("av1", "540p", 540, 960, 350.0, 440.0, 1.26, 89.0, True, "av1/540p/index.m3u8", 3),
            RenditionResult("av1", "720p", 720, 1280, 600.0, 750.0, 1.25, 93.5, True, "av1/720p/index.m3u8", 3),
        ]
        tmp_master = "/tmp/test_master_av1.m3u8"
        generate_master_playlist("av1", renditions, tmp_master, relative_prefix="av1")

        with open(tmp_master, "r") as f:
            content = f.read()

        self.assertIn("#EXTM3U", content)
        self.assertIn("#EXT-X-VERSION:7", content)
        self.assertIn("#EXT-X-INDEPENDENT-SEGMENTS", content)
        self.assertIn('CODECS="av01.0.04M.08,mp4a.40.2"', content)
        self.assertIn("BANDWIDTH=440000", content, "BANDWIDTH must reflect measured peak segment bitrate")
        self.assertIn("AVERAGE-BANDWIDTH=350000", content)


class TestHypothesesAndSavings(unittest.TestCase):

    def test_low_rung_hypothesis_1(self):
        # 360p rung should evaluate whether AV1 exceeds minimum saving threshold
        eval_res = evaluate_rung_for_clip("test_clip", "talking_head", "360p")
        self.assertIsNotNone(eval_res.bd_rate_av1_vs_h264_pct)
        saving_pct = -eval_res.bd_rate_av1_vs_h264_pct
        self.assertTrue(saving_pct >= MIN_AV1_SAVING_THRESHOLD_PCT)
        self.assertTrue(eval_res.av1_offered)

    def test_savings_calculator_arithmetic(self):
        # Section 3.1 arithmetic: 700 kbps x 60 / 8 / 1000 = 5.25 MB / min
        mb_per_min = calculate_data_per_minute(700.0)
        self.assertEqual(mb_per_min, 5.25)

        # 1,000,000 minutes at 540p: 5.25 TB H.264
        res = calculate_savings(
            cdn_price_per_gb=0.015,
            monthly_viewing_minutes=1_000_000.0,
            eligible_share_pct=40.0,
            av1_saving_pct=50.0,
            hevc_share_pct=45.0,
            hevc_saving_pct=40.0,
        )
        self.assertEqual(res["per_minute_metrics"]["h264_540p_mb_per_min"], 5.25)
        self.assertTrue(res["monthly_totals"]["total_tb_saved"] > 0)
        self.assertTrue(res["monthly_totals"]["net_annual_saved_usd"] > 0)


if __name__ == "__main__":
    unittest.main()
