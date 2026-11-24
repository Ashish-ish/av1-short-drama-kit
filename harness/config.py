"""
Configuration and constants for the AV1 Adoption Kit Transcoding Pipeline & Benchmark Harness.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RungConfig:
    name: str
    width: int
    height: int
    fps: int
    default_h264_kbps: int
    default_h264_crf: int
    default_hevc_crf: int
    default_av1_crf: int
    hardware_only: bool = False
    enabled_by_default: bool = True
    role: str = ""


# Ladder definition for 9:16 vertical short-drama video
RUNGS: Dict[str, RungConfig] = {
    "360p": RungConfig(
        name="360p",
        width=360,
        height=640,
        fps=30,
        default_h264_kbps=350,
        default_h264_crf=26,
        default_hevc_crf=28,
        default_av1_crf=38,
        hardware_only=False,
        enabled_by_default=True,
        role="Weak networks and low-tier devices",
    ),
    "540p": RungConfig(
        name="540p",
        width=540,
        height=960,
        fps=30,
        default_h264_kbps=700,
        default_h264_crf=23,
        default_hevc_crf=25,
        default_av1_crf=35,
        hardware_only=False,
        enabled_by_default=True,
        role="Default start rung for vertical feed",
    ),
    "720p": RungConfig(
        name="720p",
        width=720,
        height=1280,
        fps=30,
        default_h264_kbps=1200,
        default_h264_crf=21,
        default_hevc_crf=23,
        default_av1_crf=32,
        hardware_only=False,
        enabled_by_default=True,
        role="Strong devices and unconstrained networks",
    ),
    "1080p": RungConfig(
        name="1080p",
        width=1080,
        height=1920,
        fps=30,
        default_h264_kbps=2500,
        default_h264_crf=19,
        default_hevc_crf=21,
        default_av1_crf=29,
        hardware_only=True,
        enabled_by_default=False,
        role="Optional ultra rung: Hardware-decode devices only",
    ),
}

# Codec strings conforming to RFC 6381
CODEC_STRINGS = {
    "h264": "avc1.64001f",      # High Profile Level 3.1
    "hevc": "hvc1.1.6.L90.90",   # Main Profile Level 3.0
    "av1": "av01.0.04M.08",     # Main Profile, Level 3.0, Main tier, 8-bit
    "aac": "mp4a.40.2",         # AAC-LC
}

# Segment & GOP Settings
GOP_SECONDS = 2
SEGMENT_SECONDS = 2
TARGET_FPS = 30
MAX_PAPR_THRESHOLD = 1.8  # Maximum Peak-to-Average Bitrate Ratio allowed per rung

# Quality test points for BD-rate R-D curves (CRFs to test)
QUALITY_TEST_POINTS = {
    "h264": [19, 23, 27, 31],
    "hevc": [21, 25, 29, 33],
    "av1": [30, 34, 38, 42],
}

# Minimum AV1 bitrate reduction threshold to offer the rung (Hypothesis 1)
MIN_AV1_SAVING_THRESHOLD_PCT = 25.0
