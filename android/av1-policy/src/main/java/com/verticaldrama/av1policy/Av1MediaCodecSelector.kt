package com.verticaldrama.av1policy

import androidx.media3.common.MimeTypes
import androidx.media3.exoplayer.mediacodec.MediaCodecInfo
import androidx.media3.exoplayer.mediacodec.MediaCodecSelector
import androidx.media3.exoplayer.mediacodec.MediaCodecUtil

/**
 * Custom Media3 MediaCodecSelector that:
 * 1. Prioritizes hardware AV1 decoders.
 * 2. Explicitly opts into platform dav1d (c2.android.av1-dav1d.decoder) by name when software AV1 is allowed.
 * 3. Filters out all software AV1 decoders when policy disallows software AV1 (e.g. failed probe,
 *    thermal pressure, or cooldown), preventing ExoPlayer from erroneously counting software AV1 as supported.
 */
class Av1MediaCodecSelector(
    private val policyManager: PlaybackPolicyManager,
    private val delegate: MediaCodecSelector = MediaCodecSelector.DEFAULT,
) : MediaCodecSelector {

    companion object {
        const val DAV1D_NAME = DeviceCapabilityDetector.DAV1D_DECODER_NAME
    }

    override fun getDecoderInfos(
        mimeType: String,
        requiresSecureDecoder: Boolean,
        requiresTunnelingDecoder: Boolean,
    ): List<MediaCodecInfo> {
        val originalList = delegate.getDecoderInfos(mimeType, requiresSecureDecoder, requiresTunnelingDecoder)

        if (mimeType != MimeTypes.VIDEO_AV1) {
            return originalList
        }

        // If secure decoder required (DRM), software decoders cannot satisfy Widevine L1
        if (requiresSecureDecoder) {
            return originalList.filter { !it.softwareOnly }
        }

        val allowsSoftwareAv1 = policyManager.isSoftwareAv1Eligible()

        if (!allowsSoftwareAv1) {
            // Filter OUT software AV1 decoders completely
            return originalList.filter { !it.softwareOnly }
        }

        // When software AV1 is permitted, prioritize platform dav1d by name
        val sortedList = ArrayList<MediaCodecInfo>()
        var dav1dInfo: MediaCodecInfo? = null

        for (info in originalList) {
            if (!info.softwareOnly) {
                // Hardware decoders always come first
                sortedList.add(info)
            } else if (info.name.equals(DAV1D_NAME, ignoreCase = true)) {
                dav1dInfo = info
            }
        }

        // Place platform dav1d ahead of other generic software decoders (like libgav1)
        if (dav1dInfo != null) {
            sortedList.add(dav1dInfo)
        } else {
            // If dav1d is not in delegate list, attempt to locate it explicitly
            for (info in originalList) {
                if (info.softwareOnly) {
                    sortedList.add(info)
                }
            }
        }

        return sortedList
    }
}
