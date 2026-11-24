# ADR-001: Capped CRF and VBV instead of Pure CRF

- **Status**: Accepted
- **Date**: 2026-11-24
- **Context**: AV1 Adoption Kit for Vertical Drama Apps (v0.1)

---

## 1. Context and Problem Statement

Vertical short-drama apps operate predominantly over mobile cellular networks (4G/5G) where connection bandwidth and radio conditions fluctuate dramatically. In episodic short-drama playback, smooth startup and stall-free playback are critical for viewer retention.

Encoding video using **pure Constant Rate Factor (CRF)** produces optimal perceptual quality per average byte across an entire asset. However, pure CRF suffers from unconstrained bit distribution:
- Complex scenes—such as heavy rain, confetti, strobe lighting, fast-action motion, or dense texture—can produce instantaneous bitrate spikes 3× to 6× higher than the clip's average bitrate.
- In cellular environments, sudden multi-megabit bursts deplete the client's forward playback buffer faster than network adaptation can respond, directly triggering stalls and rebuffering events.
- Pure CRF provides no predictable ceiling for CDN egress peak bandwidth calculations or CDN edge-cache burst sizing.

Therefore, our encoding pipeline must prevent bitrate spikes while preserving the quality benefits of CRF in typical scenes.

---

## 2. Decision

We mandate **Capped CRF / VBV (Video Buffer Verifier)** across all codecs (H.264, HEVC, and AV1) in the transcoding pipeline, and explicitly prohibit pure CRF in production renditions.

### 2.1 Codec-Specific Implementations

1. **H.264 (`libx264`)**:
   - Use standard VBV capping with `-maxrate` and `-bufsize`:
     ```bash
     -c:v libx264 -crf <CRF> -maxrate <MAX_KBPS>k -bufsize <2 x MAX_KBPS>k
     ```
   - Target a buffer size equivalent to 2 seconds of maximum bitrate (`2 * maxrate`), aligning with our 2-second GOP / segment duration.

2. **HEVC (`libx265`)**:
   - Use VBV parameters matching x264 semantics:
     ```bash
     -c:v libx265 -crf <CRF> -x265-params "vbv-maxrate=<MAX_KBPS>:vbv-bufsize=<2 x MAX_KBPS>"
     ```

3. **AV1 (`libsvtav1`)**:
   - Use SVT-AV1's capped CRF feature via `mbr` (Maximum Bitrate in kbps):
     ```bash
     -c:v libsvtav1 -crf <CRF> -svtav1-params "tune=0:fast-decode=1:scd=0:mbr=<MAX_KBPS>:mbr-overshoot-pct=15"
     ```
   - **CRITICAL DISTINCTION**:
     - SVT-AV1's `buf-sz` (and related `buf-initial-sz`, `buf-optimal-sz`) options **apply to Constant Bitrate (CBR) mode only** and are expressed in **milliseconds**, NOT kilobits.
     - Specifying `buf-sz` in CRF mode has no effect or can cause unexpected encoder behavior.
     - Never copy buffer values or VBV syntax directly from `x264`/`x265` to `libsvtav1`.
     - `mbr` governs the maximum allowable bitrate in CRF mode. `mbr-overshoot-pct` configures the allowable transient overshoot (default: 15%).

### 2.2 Segment Peak-to-Average Bitrate Verification

The benchmark harness must analyze every packaged media segment:
- Compute the **Peak-to-Average Bitrate Ratio (PAPR)** for each rung and codec.
- Enforce a strict ceiling: PAPR must not exceed **1.8×** across any 2-second segment in the rendition.
- If a generated ladder rung exceeds the PAPR threshold, the harness fails the validation and requires CRF/mbr adjustment.
- The HLS Master Playlist attribute `#EXT-X-STREAM-INF:BANDWIDTH` must be derived from the **measured peak segment bitrate**, while `AVERAGE-BANDWIDTH` reflects the overall stream average. Hand-written or nominal bandwidth estimates are rejected.

---

## 3. Consequences

### Positive
- Eliminates cellular buffer depletion caused by bursty macroblock complexity.
- Accurately informs client ABR (Adaptive Bitrate) algorithms via verified `#EXT-X-STREAM-INF:BANDWIDTH` values.
- Guarantees deterministic upper bounds for CDN peak egress bandwidth and cache sizing.

### Negative / Trade-offs
- Highly complex scenes may exhibit slight perceptual quality degradation (e.g. slight softening during intense motion/rain) when the bitrate cap is reached compared to pure CRF.
- Additional harness verification pass is required to inspect every fMP4 segment.
