package com.verticaldrama.av1policy;

import android.content.Context;
import android.util.Log;

/**
 * High-level Playback Policy Coordinator per ADR-003 and ADR-004.
 */
public class PlaybackPolicyManager {

    private static final String TAG = "PlaybackPolicyManager";

    public final DeviceCapabilityDetector detector;
    public final EligibilityCache cache;
    public final Av1EligibilityProbe probe;
    public final Av1FallbackTracker fallbackTracker;

    public static class PlaybackProfile {
        public final String selectedCodec;
        public final String selectedMasterUrl;
        public final String maxRung;
        public final boolean isAv1Active;
        public final String reasonCode;

        public PlaybackProfile(
                String selectedCodec,
                String selectedMasterUrl,
                String maxRung,
                boolean isAv1Active,
                String reasonCode
        ) {
            this.selectedCodec = selectedCodec;
            this.selectedMasterUrl = selectedMasterUrl;
            this.maxRung = maxRung;
            this.isAv1Active = isAv1Active;
            this.reasonCode = reasonCode;
        }
    }

    public PlaybackPolicyManager(Context context, String appVersion) {
        this.detector = new DeviceCapabilityDetector(context);
        this.cache = new EligibilityCache(context, appVersion);
        this.probe = new Av1EligibilityProbe(context, cache);
        this.fallbackTracker = new Av1FallbackTracker(this, cache);
    }

    public PlaybackPolicyManager(Context context) {
        this(context, "1.0.0");
    }

    public boolean isSoftwareAv1Eligible() {
        if (!detector.isOsEligibleForSoftwareAv1()) {
            return false;
        }
        if (cache.isInFallbackCooldown()) {
            return false;
        }
        if (!detector.isThermalAndPowerSafe()) {
            return false;
        }
        EligibilityCache.ProbeResult probeResult = cache.getProbeResult(DeviceCapabilityDetector.DAV1D_DECODER_NAME, "540p");
        return probeResult.status == EligibilityCache.ProbeStatus.PASSED;
    }

    public PlaybackProfile getPlaybackProfile(
            String h264MasterUrl,
            String hevcMasterUrl,
            String av1MasterUrl,
            boolean hasDrm
    ) {
        // Step 1: DRM Check
        if (hasDrm) {
            DeviceCapabilityDetector.CodecSupport av1Support = detector.getAv1Support();
            if (av1Support.hasHardwareDecoder && av1MasterUrl != null) {
                return new PlaybackProfile("av1", av1MasterUrl, "720p", true, "DRM_HARDWARE_AV1_SUPPORTED");
            }
            DeviceCapabilityDetector.CodecSupport hevcSupport = detector.getHevcSupport();
            if (hevcSupport.hasHardwareDecoder && hevcMasterUrl != null) {
                return new PlaybackProfile("hevc", hevcMasterUrl, "720p", false, "DRM_HARDWARE_HEVC_FALLBACK");
            }
            return new PlaybackProfile("h264", h264MasterUrl, "720p", false, "DRM_H264_REQUIRED");
        }

        // Step 2: Hardware AV1 Check
        DeviceCapabilityDetector.CodecSupport av1Support = detector.getAv1Support();
        if (av1Support.hasHardwareDecoder && av1MasterUrl != null) {
            String maxRung = cache.getMaxAv1Rung();
            return new PlaybackProfile("av1", av1MasterUrl, maxRung, true, "HARDWARE_AV1_SELECTED");
        }

        // Step 3: Hardware HEVC Priority
        DeviceCapabilityDetector.CodecSupport hevcSupport = detector.getHevcSupport();
        if (hevcSupport.hasHardwareDecoder && hevcMasterUrl != null && !detector.isPlatformDav1dAvailable()) {
            return new PlaybackProfile("hevc", hevcMasterUrl, "720p", false, "HARDWARE_HEVC_PREFERRED");
        }

        // Step 4: Software dav1d Check
        if (av1MasterUrl != null && isSoftwareAv1Eligible()) {
            String maxRung = cache.getMaxAv1Rung();
            return new PlaybackProfile("av1", av1MasterUrl, maxRung, true, "SOFTWARE_DAV1D_ELIGIBLE");
        }

        // Step 5: Hardware HEVC Fallback
        if (hevcSupport.hasHardwareDecoder && hevcMasterUrl != null) {
            return new PlaybackProfile("hevc", hevcMasterUrl, "720p", false, "HARDWARE_HEVC_FALLBACK");
        }

        // Step 6: Guaranteed H.264 Baseline
        return new PlaybackProfile("h264", h264MasterUrl, "720p", false, "BASELINE_H264_FALLBACK");
    }
}
