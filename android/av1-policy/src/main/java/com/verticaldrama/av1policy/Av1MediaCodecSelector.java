package com.verticaldrama.av1policy;

import androidx.media3.common.MimeTypes;
import androidx.media3.exoplayer.mediacodec.MediaCodecInfo;
import androidx.media3.exoplayer.mediacodec.MediaCodecSelector;
import androidx.media3.exoplayer.mediacodec.MediaCodecUtil;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Custom Media3 MediaCodecSelector that:
 * 1. Prioritizes hardware AV1 decoders.
 * 2. Explicitly opts into platform dav1d (c2.android.av1-dav1d.decoder) by name when software AV1 is allowed.
 * 3. Filters out all software AV1 decoders when policy disallows software AV1.
 */
public class Av1MediaCodecSelector implements MediaCodecSelector {

    public static final String DAV1D_NAME = DeviceCapabilityDetector.DAV1D_DECODER_NAME;

    private final PlaybackPolicyManager policyManager;
    private final MediaCodecSelector delegate;

    public Av1MediaCodecSelector(PlaybackPolicyManager policyManager, MediaCodecSelector delegate) {
        this.policyManager = policyManager;
        this.delegate = delegate != null ? delegate : MediaCodecSelector.DEFAULT;
    }

    public Av1MediaCodecSelector(PlaybackPolicyManager policyManager) {
        this(policyManager, MediaCodecSelector.DEFAULT);
    }

    @Override
    public List<MediaCodecInfo> getDecoderInfos(
            String mimeType,
            boolean requiresSecureDecoder,
            boolean requiresTunnelingDecoder
    ) throws MediaCodecUtil.DecoderQueryException {
        List<MediaCodecInfo> originalList = delegate.getDecoderInfos(mimeType, requiresSecureDecoder, requiresTunnelingDecoder);

        if (!MimeTypes.VIDEO_AV1.equals(mimeType)) {
            return originalList;
        }

        if (requiresSecureDecoder) {
            List<MediaCodecInfo> filtered = new ArrayList<>();
            for (MediaCodecInfo info : originalList) {
                if (!info.softwareOnly) {
                    filtered.add(info);
                }
            }
            return filtered;
        }

        boolean allowsSoftwareAv1 = policyManager.isSoftwareAv1Eligible();
        if (!allowsSoftwareAv1) {
            List<MediaCodecInfo> filtered = new ArrayList<>();
            for (MediaCodecInfo info : originalList) {
                if (!info.softwareOnly) {
                    filtered.add(info);
                }
            }
            return filtered;
        }

        List<MediaCodecInfo> sortedList = new ArrayList<>();
        MediaCodecInfo dav1dInfo = null;

        for (MediaCodecInfo info : originalList) {
            if (!info.softwareOnly) {
                sortedList.add(info);
            } else if (info.name.equalsIgnoreCase(DAV1D_NAME)) {
                dav1dInfo = info;
            }
        }

        if (dav1dInfo != null) {
            sortedList.add(dav1dInfo);
        } else {
            for (MediaCodecInfo info : originalList) {
                if (info.softwareOnly) {
                    sortedList.add(info);
                }
            }
        }

        return sortedList;
    }
}
