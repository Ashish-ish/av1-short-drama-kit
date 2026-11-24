---
name: Device Qualification Report
about: Submit empirical AV1 playback benchmark data from a physical handset
title: "[QUAL] "
labels: qualification, benchmark
assignees: ''
---

**Device Information**
- Handset Manufacturer & Model: [e.g. Xiaomi Redmi Note 12, Samsung Galaxy S23]
- Chipset / SoC: [e.g. Snapdragon 685, Dimensity 7050]
- OS Version: [e.g. Android 13, iOS 17.4]
- Decoder Identified: [e.g. `c2.android.av1-dav1d.decoder`, `c2.qcom.av1.decoder`, `Apple A17 Pro HW`]

**Benchmark Results**
- Resolution Tested: [360p / 540p / 720p / 1080p]
- Average Time-To-First-Frame (TTFF): [e.g. 142 ms]
- Decoder Initialization Latency: [e.g. 18 ms]
- Average Dropped Frames per Minute: [e.g. 0.0 drops/min]
- Playback Session Duration: [e.g. 15 minutes, 30 episodes]
- Peak Battery Temperature: [e.g. 34.2°C]

**Recommendation**
- [ ] Safe for default software AV1 (dav1d)
- [ ] Hardware AV1 verified
- [ ] Recommend fallback to hardware HEVC or H.264
