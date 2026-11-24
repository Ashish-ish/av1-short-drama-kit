package com.verticaldrama.av1policy

import android.content.Context
import android.util.Log

/**
 * High-level Playback Policy Coordinator.
 * Evaluates device capabilities, cache status, DRM requirements, and environmental safety
 * to select the optimal stream master and maximum rung per ADR-003 and ADR-004.
 */
class PlaybackPolicyManager(
    private val context: Context,
    val appVersion: String = "1.0.0",
) {
    companion object {
        private const val TAG = "PlaybackPolicyManager"
    }

    val detector = DeviceCapabilityDetector(context)
    val cache = EligibilityCache(context, appVersion)
    val probe = Av1EligibilityProbe(context, cache)
    val fallbackTracker = Av1FallbackTracker(this, cache)

    data class PlaybackProfile(
        val selectedCodec: String,        // "av1", "hevc", "h264"
        val selectedMasterUrl: String,
        val maxRung: String,              // "720p", "540p", "360p"
        val isAv1Active: Boolean,
        val reasonCode: String,
    )

    /**
     * Determines whether software AV1 decoding is permitted for this device session.
     */
    fun isSoftwareAv1Eligible(): Boolean {
        // 1. Device must be Android 12+ (API 31+)
        if (!detector.isOsEligibleForSoftwareAv1()) {
            return false
        }

        // 2. Cooldown check: no more than 3 fallbacks in last 24h
        if (cache.isInFallbackCooldown()) {
            return false
        }

        // 3. Environment check: battery saver must be off, thermal status normal
        if (!detector.isThermalAndPowerSafe()) {
            return false
        }

        // 4. Must pass probe benchmark on at least 360p or 540p
        val probeResult = cache.getProbeResult(DeviceCapabilityDetector.DAV1D_DECODER_NAME, "540p")
        return probeResult.status == EligibilityCache.ProbeStatus.PASSED
    }

    /**
     * Core master selection algorithm per ADR-003:
     * Priority: Hardware AV1 -> Hardware HEVC -> Software dav1d -> H.264 Baseline
     */
    fun getPlaybackProfile(
        h264MasterUrl: String,
        hevcMasterUrl: String? = null,
        av1MasterUrl: String? = null,
        hasDrm: Boolean = false,
    ): PlaybackProfile {
        // Step 1: DRM Check. Software decoders lack Widevine L1.
        if (hasDrm) {
            val av1Support = detector.getAv1Support()
            if (av1Support.hasHardwareDecoder && av1MasterUrl != null) {
                return PlaybackProfile(
                    selectedCodec = "av1",
                    selectedMasterUrl = av1MasterUrl,
                    maxRung = "720p",
                    isAv1Active = true,
                    reasonCode = "DRM_HARDWARE_AV1_SUPPORTED"
                )
            }
            val hevcSupport = detector.getHevcSupport()
            if (hevcSupport.hasHardwareDecoder && hevcMasterUrl != null) {
                return PlaybackProfile(
                    selectedCodec = "hevc",
                    selectedMasterUrl = hevcMasterUrl,
                    maxRung = "720p",
                    isAv1Active = false,
                    reasonCode = "DRM_HARDWARE_HEVC_FALLBACK"
                )
            }
            return PlaybackProfile(
                selectedCodec = "h264",
                selectedMasterUrl = h264MasterUrl,
                maxRung = "720p",
                isAv1Active = false,
                reasonCode = "DRM_H264_REQUIRED"
            )
        }

        // Step 2: Hardware AV1 Check
        val av1Support = detector.getAv1Support()
        if (av1Support.hasHardwareDecoder && av1MasterUrl != null) {
            val maxRung = cache.getMaxAv1Rung()
            return PlaybackProfile(
                selectedCodec = "av1",
                selectedMasterUrl = av1MasterUrl,
                maxRung = maxRung,
                isAv1Active = true,
                reasonCode = "HARDWARE_AV1_ELIGIBLE"
            )
        }

        // Step 3: Hardware HEVC Check (captures ~44% savings with zero risk)
        val hevcSupport = detector.getHevcSupport()
        if (hevcSupport.hasHardwareDecoder && hevcMasterUrl != null && !isSoftwareAv1Eligible()) {
            return PlaybackProfile(
                selectedCodec = "hevc",
                selectedMasterUrl = hevcMasterUrl,
                maxRung = "720p",
                isAv1Active = false,
                reasonCode = "PREFER_HARDWARE_HEVC"
            )
        }

        // Step 4: Software AV1 (dav1d) Check
        if (av1MasterUrl != null) {
            if (cache.isInFallbackCooldown()) {
                Log.i(TAG, "Device in 7-day fallback cooldown. Serving H.264.")
                return PlaybackProfile(
                    selectedCodec = "h264",
                    selectedMasterUrl = h264MasterUrl,
                    maxRung = "720p",
                    isAv1Active = false,
                    reasonCode = "COOLDOWN_ACTIVE_SERVE_H264"
                )
            }

            if (!detector.isOsEligibleForSoftwareAv1()) {
                return PlaybackProfile(
                    selectedCodec = "h264",
                    selectedMasterUrl = h264MasterUrl,
                    maxRung = "720p",
                    isAv1Active = false,
                    reasonCode = "OS_INELIGIBLE_FOR_DAV1D"
                )
            }

            if (!detector.isThermalAndPowerSafe()) {
                return PlaybackProfile(
                    selectedCodec = "h264",
                    selectedMasterUrl = h264MasterUrl,
                    maxRung = "720p",
                    isAv1Active = false,
                    reasonCode = "THERMAL_OR_POWER_SAVER_ACTIVE"
                )
            }

            val probe540p = cache.getProbeResult(DeviceCapabilityDetector.DAV1D_DECODER_NAME, "540p")
            if (probe540p.status == EligibilityCache.ProbeStatus.PASSED) {
                val maxRung = cache.getMaxAv1Rung()
                return PlaybackProfile(
                    selectedCodec = "av1",
                    selectedMasterUrl = av1MasterUrl,
                    maxRung = maxRung,
                    isAv1Active = true,
                    reasonCode = "SOFTWARE_DAV1D_PROBE_PASSED"
                )
            } else if (probe540p.status == EligibilityCache.ProbeStatus.UNKNOWN) {
                // Trigger background probe if not already triggered
                probe.runProbe("540p")
                return PlaybackProfile(
                    selectedCodec = "h264",
                    selectedMasterUrl = h264MasterUrl,
                    maxRung = "720p",
                    isAv1Active = false,
                    reasonCode = "PROBE_PENDING_SERVE_H264"
                )
            }
        }

        // Step 5: Default Safe Baseline
        return PlaybackProfile(
            selectedCodec = "h264",
            selectedMasterUrl = h264MasterUrl,
            maxRung = "720p",
            isAv1Active = false,
            reasonCode = "DEFAULT_H264_BASELINE"
        )
    }
}
