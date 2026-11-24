import Foundation
import VideoToolbox
import CoreMedia

/// Playback Codec Types
public enum PlaybackCodec: String, Codable {
    case h264 = "h264"
    case hevc = "hevc"
    case av1 = "av1"
}

/// Profile outcome returned by AV1PolicyManager
public struct PlaybackProfile {
    public let selectedURL: URL
    public let codec: PlaybackCodec
    public let maxRung: String
    public let isHardwareDecode: Bool
    public let reasonCode: String

    public init(
        selectedURL: URL,
        codec: PlaybackCodec,
        maxRung: String,
        isHardwareDecode: Bool,
        reasonCode: String
    ) {
        self.selectedURL = selectedURL
        self.codec = codec
        self.maxRung = maxRung
        self.isHardwareDecode = isHardwareDecode
        self.reasonCode = reasonCode
    }
}

/// iOS Hardware-Only Playback Policy Manager.
///
/// Under iOS, AVPlayer cannot bind third-party software decoders.
/// Software AV1 on iOS is out of scope as it forfeits AirPlay, Picture-in-Picture,
/// FairPlay DRM, and system hardware scaling.
///
/// On iOS, the kit functions strictly as future-proofing:
/// - Devices with verified hardware AV1 decode receive the AV1 master playlist.
/// - Devices without hardware AV1 decode remain on H.264 (or hardware HEVC).
/// - No iPhone model lists are hardcoded; runtime VTIsHardwareDecodeSupported governs eligibility.
public class AV1PolicyManager {

    public static let shared = AV1PolicyManager()

    /// FourCC for AV1 ('av01' = 0x61763031)
    private let kCMVideoCodecType_AV1_Custom: CMVideoCodecType = 0x61763031

    public init() {}

    /// Checks if the current iOS hardware System-on-Chip provides native hardware AV1 decode.
    public func isHardwareAV1Supported() -> Bool {
        return VTIsHardwareDecodeSupported(kCMVideoCodecType_AV1_Custom)
    }

    /// Checks if the current iOS device supports hardware HEVC decode.
    public func isHardwareHEVCSupported() -> Bool {
        return VTIsHardwareDecodeSupported(kCMVideoCodecType_HEVC)
    }

    /// Selects the optimal master playlist URL and codec per policy rules.
    public func getPlaybackProfile(
        h264Master: URL,
        hevcMaster: URL? = nil,
        av1Master: URL? = nil
    ) -> PlaybackProfile {
        // 1. Hardware AV1 Check
        if let av1URL = av1Master, isHardwareAV1Supported() {
            return PlaybackProfile(
                selectedURL: av1URL,
                codec: .av1,
                maxRung: "720p",
                isHardwareDecode: true,
                reasonCode: "IOS_HARDWARE_AV1_SUPPORTED"
            )
        }

        // 2. Hardware HEVC Check
        if let hevcURL = hevcMaster, isHardwareHEVCSupported() {
            return PlaybackProfile(
                selectedURL: hevcURL,
                codec: .hevc,
                maxRung: "720p",
                isHardwareDecode: true,
                reasonCode: "IOS_HARDWARE_HEVC_FALLBACK"
            )
        }

        // 3. Baseline H.264
        return PlaybackProfile(
            selectedURL: h264Master,
            codec: .h264,
            maxRung: "720p",
            isHardwareDecode: true,
            reasonCode: "IOS_DEFAULT_H264"
        )
    }
}
