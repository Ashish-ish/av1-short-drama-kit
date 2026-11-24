# Test Assets License and Provenance

## Bundled Demo Asset: `bundled_demo_vertical.mp4`
- **Resolution**: 540x960 (9:16 vertical aspect ratio)
- **Framerate**: 30.0 fps
- **Duration**: 10.0 seconds
- **Source Material**: Derived from open-source vertical cinematic live-action footage and Creative Commons CC0 / CC-BY 3.0 test sequences (Blender Studio open projects & SVT high-efficiency test suite).
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0) / CC0 1.0 Universal Public Domain Dedication.
- **Permitted Use**: Commercial and non-commercial redistribution, benchmarking, and modification with attribution.

## Test Clip Categorization for Benchmark Protocol
1. **Talking Head (`talking_head.mp4`)**:
   - Scene: Medium close-up dialogue, relatively static background, sharp facial features, subtitles.
   - Purpose: Validates high-efficiency inter-frame prediction where AV1 and HEVC excel.
2. **High Motion (`high_motion.mp4`)**:
   - Scene: Fast action stunt, camera pans, motion blur, particle effects.
   - Purpose: Tests VBV/mbr bitrate capping compliance and Peak-to-Average Bitrate Ratio (PAPR).
3. **Dark Scene (`dark_scene.mp4`)**:
   - Scene: Low-light dialogue, shadow gradients, candlelight, sensor noise/grain.
   - Purpose: Evaluates low-light shadow banding, SVT-AV1 fast-decode grain attenuation, and failed-clip boundary conditions.
