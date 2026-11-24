# ADR-002: Lazy Decoder Initialisation with Decoupled Network Preload

- **Status**: Accepted
- **Date**: 2026-11-24
- **Context**: AV1 Adoption Kit for Vertical Drama Apps (v0.1)

---

## 1. Context and Problem Statement

Vertical short-drama apps rely heavily on a vertical swipe feed where episodes (typically 60 to 90 seconds each) transition seamlessly. Meeting the target Time-To-First-Frame (TTFF) of under 200 milliseconds requires aggressive preloading of upcoming episodes (Episode $N+1$, $N+2$).

However, naive player architectures conflate **network preloading** with **decoder instantiation**:
1. **Decoder Instance Exhaustion**: Mobile System-on-Chips (SoCs) enforce hard limits on concurrent hardware `MediaCodec` instances (often as low as 2 to 4 concurrent video decoder sessions). Exceeding this limit causes `MediaCodec.CodecException` (`ERROR_INSUFFICIENT_RESOURCE`).
2. **Software Decoder CPU Thrashing**: On devices without hardware AV1 decoding, Android uses platform software decoding (`dav1d`). Initializing and decoding frames on two concurrent software AV1 decoders (the active episode and a pre-warmed upcoming episode) causes immediate CPU core saturation, thermal throttling, and severe frame drops on the actively watched video.
3. **Memory Footprint**: Forward-allocated decoder frame buffers (YUV surfaces) consume significant graphics/system memory, increasing the likelihood of Low Memory Killer (LMK) termination.

---

## 2. Decision

We mandate strict **decoupling of network data preloading from codec decoder initialization**:

```
[Feed Controller / Swipe Engine]
               │
               ▼
   [Network Preload Layer]
(DefaultPreloadManager + TargetPreloadStatusControl)
               │  Downloads init.mp4 + first 2-4s segments to disk/cache
               ▼
         [Disk Cache]
               │
      [Episode Transition] ──► Lazy Decoder Initialization
                               (Triggered ONLY on user focus/settle)
                                       │
                                       ▼
                             [Single Active MediaCodec]
                             (dav1d / Hardware MediaCodec)
```

### 2.1 Decoupled Network Preload
- Use Android Media3's `DefaultPreloadManager` configured with a custom `TargetPreloadStatusControl`.
- Preload status is restricted to network segment retrieval: fetching the fMP4 initialization segment (`init.mp4`) and the first 2 to 4 seconds of media segments into `SimpleCache`.
- The preload manager is explicitly prohibited from calling `player.prepare()` or binding to a `SurfaceView` before the item becomes active.

### 2.2 Lazy Codec Initialisation
- A `MediaCodec` video decoder instance is initialized **lazily** only when the user commits to viewing an episode (e.g. when a vertical swipe gesture crosses the 50% paging threshold or on pager idle).
- **Rule of One Software Decoder**: Under no circumstances shall two software AV1 decoders run concurrently. The previous episode's player/codec must release its `MediaCodec` session before the incoming software AV1 decoder acquires its instance.
- **Decoder-Init Latency Budget**: Benchmark instrumentation must monitor `onVideoDecoderInitialized` latency. In production, platform `dav1d` initialization typically consumes 12–35 ms on modern ARM64 devices, leaving ample headroom inside the 200 ms TTFF budget when reading preloaded segments from local disk cache.

---

## 3. Consequences

### Positive
- Prevents `MediaCodec` resource exhaustion across low- and mid-tier Android devices.
- Eliminates CPU contention and dropped frames during episode transitions.
- Minimizes background battery drain and heat generation while browsing the drama feed.
- Respects device instance limits and allows clean fallback if resource allocation fails.

### Negative / Trade-offs
- Time-To-First-Frame cannot benefit from pre-decoded initial frames; it must rely entirely on fast disk I/O, small init segments, and rapid decoder startup.
- Requires precise lifecycle management in the Android `RecyclerView` / `ViewPager2` integration.
