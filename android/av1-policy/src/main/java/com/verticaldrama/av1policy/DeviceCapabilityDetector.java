package com.verticaldrama.av1policy;

import android.content.Context;
import android.media.MediaCodecInfo;
import android.media.MediaCodecList;
import android.media.MediaFormat;
import android.os.Build;
import android.os.PowerManager;

/**
 * Detects hardware and software video codec capabilities, OS versions,
 * thermal state, and battery saver conditions per ADR-003 and ADR-004.
 */
public class DeviceCapabilityDetector {

    public static final String MIME_AV1 = "video/av01";
    public static final String MIME_HEVC = "video/hevc";
    public static final String MIME_AVC = "video/avc";
    public static final String DAV1D_DECODER_NAME = "c2.android.av1-dav1d.decoder";

    private final Context context;

    public static class CodecSupport {
        public final String mimeType;
        public final boolean hasHardwareDecoder;
        public final String hardwareDecoderName;
        public final boolean hasSoftwareDecoder;
        public final String softwareDecoderName;
        public final int maxSupportedWidth;
        public final int maxSupportedHeight;

        public CodecSupport(
                String mimeType,
                boolean hasHardwareDecoder,
                String hardwareDecoderName,
                boolean hasSoftwareDecoder,
                String softwareDecoderName,
                int maxSupportedWidth,
                int maxSupportedHeight
        ) {
            this.mimeType = mimeType;
            this.hasHardwareDecoder = hasHardwareDecoder;
            this.hardwareDecoderName = hardwareDecoderName;
            this.hasSoftwareDecoder = hasSoftwareDecoder;
            this.softwareDecoderName = softwareDecoderName;
            this.maxSupportedWidth = maxSupportedWidth;
            this.maxSupportedHeight = maxSupportedHeight;
        }
    }

    public DeviceCapabilityDetector(Context context) {
        this.context = context.getApplicationContext();
    }

    public CodecSupport getAv1Support() {
        return detectSupportForMime(MIME_AV1);
    }

    public CodecSupport getHevcSupport() {
        return detectSupportForMime(MIME_HEVC);
    }

    public CodecSupport getH264Support() {
        return detectSupportForMime(MIME_AVC);
    }

    private CodecSupport detectSupportForMime(String mime) {
        boolean hasHw = false;
        String hwName = null;
        boolean hasSw = false;
        String swName = null;
        int maxWidth = 0;
        int maxHeight = 0;

        MediaCodecList codecList = new MediaCodecList(MediaCodecList.REGULAR_CODECS);
        for (MediaCodecInfo info : codecList.getCodecInfos()) {
            if (info.isEncoder()) continue;
            for (String type : info.getSupportedTypes()) {
                if (type.equalsIgnoreCase(mime)) {
                    boolean isSoftware;
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                        isSoftware = info.isSoftwareOnly();
                    } else {
                        String name = info.getName().toLowerCase();
                        isSoftware = name.startsWith("omx.google.") || name.startsWith("c2.android.");
                    }

                    MediaCodecInfo.CodecCapabilities caps = info.getCapabilitiesForType(mime);
                    if (caps != null && caps.getVideoCapabilities() != null) {
                        maxWidth = Math.max(maxWidth, caps.getVideoCapabilities().getSupportedWidths().getUpper());
                        maxHeight = Math.max(maxHeight, caps.getVideoCapabilities().getSupportedHeights().getUpper());
                    }

                    if (isSoftware) {
                        hasSw = true;
                        swName = info.getName();
                    } else {
                        hasHw = true;
                        hwName = info.getName();
                    }
                }
            }
        }

        return new CodecSupport(mime, hasHw, hwName, hasSw, swName, maxWidth, maxHeight);
    }

    public boolean isPlatformDav1dAvailable() {
        MediaCodecList codecList = new MediaCodecList(MediaCodecList.REGULAR_CODECS);
        for (MediaCodecInfo info : codecList.getCodecInfos()) {
            if (!info.isEncoder() && info.getName().equalsIgnoreCase(DAV1D_DECODER_NAME)) {
                return true;
            }
        }
        return false;
    }

    public boolean isOsEligibleForSoftwareAv1() {
        return Build.VERSION.SDK_INT >= 31; // Android 12+ per ADR-004
    }

    public boolean isBatterySaverActive() {
        PowerManager pm = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
        return pm != null && pm.isPowerSaveMode();
    }

    public boolean isThermalThrottling() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            PowerManager pm = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
            if (pm != null) {
                int status = pm.getCurrentThermalStatus();
                return status >= PowerManager.THERMAL_STATUS_MODERATE;
            }
        }
        return false;
    }

    public boolean isThermalAndPowerSafe() {
        return !isBatterySaverActive() && !isThermalThrottling();
    }
}
