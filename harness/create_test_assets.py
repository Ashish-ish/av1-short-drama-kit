"""
Creates minimal compliant MP4 test assets for the benchmark harness and demo encodes.
"""

import os
import struct


def make_minimal_mp4(width: int = 540, height: int = 960, duration_sec: int = 10) -> bytes:
    """Constructs a minimal valid ISO BMFF MP4 header with video track atoms."""
    # ftyp box
    ftyp_payload = b"isom" + struct.pack(">I", 512) + b"isomiso2mp41"
    ftyp = struct.pack(">I", len(ftyp_payload) + 8) + b"ftyp" + ftyp_payload

    # mvhd box
    time_scale = 1000
    duration_units = duration_sec * time_scale
    mvhd_payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + struct.pack(">II", 0, 0)  # creation/mod time
        + struct.pack(">II", time_scale, duration_units)
        + struct.pack(">I", 0x00010000)  # rate 1.0
        + struct.pack(">H", 0x0100)  # volume 1.0
        + b"\x00" * 10  # reserved
        + struct.pack(">9I", 0x00010000, 0, 0, 0, 0x00010000, 0, 0, 0, 0x40000000)  # identity matrix
        + b"\x00" * 24  # pre_defined
        + struct.pack(">I", 2)  # next_track_ID
    )
    mvhd = struct.pack(">I", len(mvhd_payload) + 8) + b"mvhd" + mvhd_payload

    # tkhd box
    tkhd_payload = (
        b"\x00\x00\x00\x07"  # version/flags (enabled, in movie, in preview)
        + struct.pack(">II", 0, 0)  # creation/mod time
        + struct.pack(">I", 1)  # track ID 1
        + struct.pack(">I", 0)  # reserved
        + struct.pack(">I", duration_units)
        + b"\x00" * 8  # reserved
        + struct.pack(">H", 0)  # layer
        + struct.pack(">H", 0)  # alternate group
        + struct.pack(">H", 0)  # volume
        + struct.pack(">H", 0)  # reserved
        + struct.pack(">9I", 0x00010000, 0, 0, 0, 0x00010000, 0, 0, 0, 0x40000000)
        + struct.pack(">II", width << 16, height << 16)  # width, height
    )
    tkhd = struct.pack(">I", len(tkhd_payload) + 8) + b"tkhd" + tkhd_payload

    # mdhd box
    mdhd_payload = (
        b"\x00\x00\x00\x00"
        + struct.pack(">II", 0, 0)
        + struct.pack(">II", 30, duration_sec * 30)  # 30 fps
        + struct.pack(">H", 0x55C4)  # lang 'und'
        + struct.pack(">H", 0)
    )
    mdhd = struct.pack(">I", len(mdhd_payload) + 8) + b"mdhd" + mdhd_payload

    # hdlr box
    hdlr_payload = (
        b"\x00\x00\x00\x00"
        + b"\x00" * 4
        + b"vide"
        + b"\x00" * 12
        + b"VideoHandler\x00"
    )
    hdlr = struct.pack(">I", len(hdlr_payload) + 8) + b"hdlr" + hdlr_payload

    # vmhd
    vmhd = struct.pack(">I", 20) + b"vmhd" + b"\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00"
    # dinf / dref
    dref = struct.pack(">I", 28) + b"dref" + b"\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x0c" + b"url \x00\x00\x00\x01"
    dinf = struct.pack(">I", len(dref) + 8) + b"dinf" + dref
    # stbl
    stts = struct.pack(">I", 24) + b"stts" + b"\x00\x00\x00\x00\x00\x00\x00\x01" + struct.pack(">II", duration_sec * 30, 1)
    stsc = struct.pack(">I", 16) + b"stsc" + b"\x00\x00\x00\x00\x00\x00\x00\x00"
    stsz = struct.pack(">I", 20) + b"stsz" + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    stco = struct.pack(">I", 16) + b"stco" + b"\x00\x00\x00\x00\x00\x00\x00\x00"
    stsd = struct.pack(">I", 16) + b"stsd" + b"\x00\x00\x00\x00\x00\x00\x00\x00"
    stbl_payload = stsd + stts + stsc + stsz + stco
    stbl = struct.pack(">I", len(stbl_payload) + 8) + b"stbl" + stbl_payload

    minf_payload = vmhd + dinf + stbl
    minf = struct.pack(">I", len(minf_payload) + 8) + b"minf" + minf_payload

    mdia_payload = mdhd + hdlr + minf
    mdia = struct.pack(">I", len(mdia_payload) + 8) + b"mdia" + mdia_payload

    trak_payload = tkhd + mdia
    trak = struct.pack(">I", len(trak_payload) + 8) + b"trak" + trak_payload

    moov_payload = mvhd + trak
    moov = struct.pack(">I", len(moov_payload) + 8) + b"moov" + moov_payload

    # mdat with synthetic video data (~50 KB)
    mdat_size = 50 * 1024
    mdat = struct.pack(">I", mdat_size) + b"mdat" + (b"\xaa\x55\x33\xcc" * (mdat_size // 4 - 2))

    return ftyp + moov + mdat


def create_all_test_assets(target_dir: str = "test_assets"):
    os.makedirs(target_dir, exist_ok=True)
    clips = [
        ("bundled_demo_vertical.mp4", 540, 960),
        ("talking_head.mp4", 540, 960),
        ("high_motion.mp4", 540, 960),
        ("dark_scene.mp4", 540, 960),
    ]
    for name, w, h in clips:
        path = os.path.join(target_dir, name)
        data = make_minimal_mp4(w, h, duration_sec=10)
        with open(path, "wb") as f:
            f.write(data)
        print(f"Created {path} ({len(data)} bytes)")


if __name__ == "__main__":
    create_all_test_assets()
