# ADR-004: Client Eligibility Thresholds, Background Probe, and Runtime Fallback

- **Status**: Accepted
- **Date**: 2026-11-24
- **Context**: AV1 Adoption Kit for Vertical Drama Apps (v0.1)

---

## 1. Context and Problem Statement

Deploying software AV1 decoding (`dav1d`) on mobile Android devices requires strict safety rails. Unlike hardware decoders, software decoding relies on the application processor (AP). On low-tier SoCs (such as older octa-core ARM Cortex-A53 clusters), decoding 720p30 or 1080p30 in software can exhaust CPU budget, cause sustained frame drops (>5%), induce thermal throttling, and drain battery life.

The kit's core operating principle is: **"Never worse than the H.264 baseline."**
AV1 must only be delivered to devices that demonstrate reliable, real-time playback capability without thermal or battery distress. Furthermore, if any unexpected runtime issue occurs during playback, the player must seamlessly degrade to H.264 without interrupting the user.

---

## 2. Decision

We establish an end-to-end client eligibility pipeline, an off-critical-path background benchmark probe, and deterministic runtime fallback rules.

### 2.1 Complete Eligibility Flow

```mermaid
flowchart TD
    Start[Content Playback Request] --> DRM{DRM Protected?}
    DRM -- Yes --> H264_Only[Serve H.264 Ladder<br/>(Software lacks L1 DRM)]
    DRM -- No --> HW_AV1{Hardware AV1 Decoder<br/>Supports Rung?}
    HW_AV1 -- Yes --> AV1_Eligible[Mark Rung Eligible for Hardware AV1]
    HW_AV1 -- No --> OS_Check{Android 12+ / API 31+<br/>or verified Android 11?}
    OS_Check -- No --> H264_Fallback[Serve H.264 Master]
    OS_Check -- Yes --> EnvCheck{Battery Saver OFF &<br/>Thermal Status < MODERATE?}
    EnvCheck -- No --> H264_Fallback
    EnvCheck -- Yes --> CacheCheck{Cached Probe Result<br/>Valid for Build & Decoder?}
    CacheCheck -- "Yes (Passed)" --> AV1_Eligible_SW[Mark Rung Eligible for dav1d]
    CacheCheck -- "Yes (Failed)" --> H264_Fallback
    CacheCheck -- "No / Pending" --> LaunchProbe[Enqueue Background Probe<br/>Serve H.264 in Interim]
```

### 2.2 Background Benchmark Probe Rules

To verify that software AV1 decoding is fast enough without risking playback jank:
1. **Never on the Critical Path**:
   - The probe runs asynchronously during idle app states (e.g. `WorkManager` or post-startup idle).
   - The probe is strictly inhibited while active video playback is in progress.
   - Initial playback always serves H.264 until the probe completes and passes.
2. **Surface & Codec Disposal**:
   - Decode using a null output surface (or off-screen `ByteBuffer` output).
   - Wrap all codec execution in a strict `try-finally` block to ensure `MediaCodec.release()` is called immediately upon completion or exception.
3. **Target Decoder**:
   - Explicitly query and select `c2.android.av1-dav1d.decoder` by name. Do not assume dav1d is the system default.
4. **Time-Boxing and Metrics**:
   - Feed a bundled 3-second vertical AV1 sample clip (encoded with `fast-decode=1`, 30 fps at candidate rung).
   - Time-box the probe execution to a maximum of 5,000 ms.
   - **Pass Criterion**: The effective decode speed must reach or exceed **1.5× real-time** (i.e. $\ge 45$ frames per second for a 30 fps master) with zero unrecovered frame drops.
5. **Transient Resource Handling**:
   - System resource limits vary dynamically. If `MediaCodec.CodecException` occurs with error code `ERROR_INSUFFICIENT_RESOURCE`, treat status as **UNKNOWN (Transient)**.
   - Do **NOT** permanently blacklist the device. Schedule a retry with exponential backoff and serve H.264 in the interim.
6. **Result Caching**:
   - Cache results locally keyed by:
     `{device_fingerprint, os_build_id, decoder_name, app_version, rung}`.
   - Invalidate cache upon OS update or app upgrade.

### 2.3 Rung Capping
Probe rungs progressively from lowest to highest (360p $\rightarrow$ 540p $\rightarrow$ 720p):
- The highest rung that passes the $\ge 1.5\times$ threshold becomes `max_av1_rung`.
- Higher rungs are served via H.264 only.
- 1080p is restricted to hardware decode only and disabled by default.

### 2.4 Runtime Fallback Rules

| Trigger | Action | Recovery & Penalty |
| :--- | :--- | :--- |
| **Decoder Initialization Failure** or Fatal Error | Instant seamless switch to H.264 master playlist at current playback PTS | Log error with reason code; retry probe after app restart. |
| **Sustained Frame Drops** (> 5% dropped frames over trailing 10s window) | Trigger mid-stream fallback to H.264 master | Reduce `max_av1_rung` by one rung tier for 24 hours. |
| **Repeated Buffer Stalls** (2+ stalls within 15 seconds not caused by network bandwidth) | Trigger mid-stream fallback to H.264 master | Record fallback reason code. |
| **3 Fallbacks within 24 Hours** | Complete deactivation of AV1 for the device | Fallback cooldown: device remains on H.264 for 7 days before probe re-test. |

### 2.5 Dynamic Tuning via Remote Config
Thresholds are parameterized for remote configuration tuning:
- `probe_speed_multiplier_min`: default `1.5`
- `max_dropped_frame_pct`: default `5.0%`
- `fallback_cooldown_days`: default `7`
- `max_consecutive_fallbacks`: default `3`

---

## 3. Consequences

### Positive
- Prevents janky playback and app unresponsiveness on budget mobile hardware.
- Protects users from overheating and excessive battery consumption.
- Gracefully handles transient Android codec resource constraints without permanent lockouts.

### Negative / Trade-offs
- First-session users on eligible devices experience H.264 until the background probe completes.
- Caching probe state introduces minimal local storage requirements (~1 KB in SharedPreferences/DataStore).
