package com.verticaldrama.av1policy

import android.content.Context
import android.media.MediaCodecInfo
import android.media.MediaCodecList
import android.media.MediaFormat
import android.os.Build
import android.os.PowerManager

/**
 * Detects hardware and software video codec capabilities, OS versions,
 * thermal state, and battery saver conditions.
 */
class DeviceCapabilityDetector(private val context: Context) {

    companion object {
        const val MIME_AV1 = MediaFormat.MIMETYPE_VIDEO_AV1
        const val MIME_HEVC = MediaFormat.MIMETYPE_VIDEO_HEVC
        const val MIME_AVC = MediaFormat.MIMETYPE_VIDEO_AVC
        const val DAV1D_DECODER_NAME = "c2.android.av1-dav1d.decoder"
    }

    data class CodecSupport(
        val mimeType: String,
        val hasHardwareDecoder: Boolean,
        val hardwareDecoderName: String?,
        val hasSoftwareDecoder: Boolean,
        val softwareDecoderName: String?,
        val maxSupportedWidth: Int,
        val maxSupportedHeight: Int,
    )

    fun getAv1Support(): CodecSupport = detectSupportForMime(MIME_AV1)

    fun getHevcSupport(): CodecSupport = detectSupportForMime(MIME_HEVC)

    fun getH264Support(): CodecSupport = detectSupportForMime(MIME_AVC)

    /**
     * Inspects MediaCodecList to identify hardware and software decoders.
     */
    private fun detectSupportForMime(mime: String): CodecSupport {
        var hasHw = false
        var hwName: String? = null
        var hasSw = false
        var swName: String? = null
        var maxWidth = 0
        var maxHeight = 0

        val codecList = MediaCodecList(MediaCodecList.REGULAR_CODECS)
        for (info in codecList.codecInfos) {
            if (info.isEncoder) continue
            val types = info.supportedTypes
            for (type in types) {
                if (type.equals(mime, ignoreCase = true)) {
                    val isSoftware = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                        info.isSoftwareOnly
                    } else {
                        val name = info.name.lowercase()
                        name.startsWith("omx.google.") || name.startsWith("c2.android.")
                    }

                    val caps = info.getCapabilitiesForType(mime)
                    val videoCaps = caps.videoCapabilities
                    if (videoCaps != null) {
                        maxWidth = maxOf(maxWidth, videoCaps.supportedWidths.upper)
                        maxHeight = maxOf(maxHeight, videoCaps.supportedHeights.upper)
                    }

                    if (isSoftware) {
                        hasSw = true
                        swName = info.name
                    } else {
                        hasHw = true
                        hwName = info.name
                    }
                }
            }
        }

        return CodecSupport(
            mimeType = mime,
            hasHardwareDecoder = hasHw,
            hardwareDecoderName = hwName,
            hasSoftwareDecoder = hasSw,
            softwareDecoderName = swName,
            maxSupportedWidth = maxWidth,
            maxSupportedHeight = maxHeight,
        )
    }

    /**
     * Checks if platform dav1d is available on this device by explicit name.
     */
    fun isPlatformDav1dAvailable(): Boolean {
        val codecList = MediaCodecList(MediaCodecList.REGULAR_CODECS)
        for (info in codecList.codecInfos) {
            if (!info.isEncoder && info.name.equals(DAV1D_DECODER_NAME, ignoreCase = true)) {
                return true
            }
        }
        return false
    }

    /**
     * Android 12 (API 31) or higher where platform dav1d arrived through Play system updates.
     */
    fun isOsEligibleForSoftwareAv1(): Boolean {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
    }

    /**
     * Verifies that battery saver is off and thermal state is below moderate.
     */
    fun isThermalAndPowerSafe(): Boolean {
        val powerManager = context.getSystemService(Context.POWER_SERVICE) as? PowerManager ?: return true

        if (powerManager.isPowerSaveMode) {
            return false
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val thermalStatus = powerManager.currentThermalStatus
            if (thermalStatus >= PowerManager.THERMAL_STATUS_MODERATE) {
                return false
            }
        }

        return true
    }
}
