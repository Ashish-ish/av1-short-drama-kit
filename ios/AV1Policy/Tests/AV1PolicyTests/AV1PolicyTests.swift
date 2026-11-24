import XCTest
@testable import AV1Policy

final class AV1PolicyTests: XCTestCase {

    func testPolicyManagerSelection() {
        let manager = AV1PolicyManager()
        let h264 = URL(string: "https://cdn.example.com/master_h264.m3u8")!
        let hevc = URL(string: "https://cdn.example.com/master_hevc.m3u8")!
        let av1 = URL(string: "https://cdn.example.com/master_av1.m3u8")!

        let profile = manager.getPlaybackProfile(h264Master: h264, hevcMaster: hevc, av1Master: av1)

        // On current macOS or iOS runner, verify that profile returned is valid
        XCTAssertNotNil(profile.selectedURL)
        XCTAssertFalse(profile.reasonCode.isEmpty)
        XCTAssertEqual(profile.maxRung, "720p")
    }

    func testBaselineFallbackURL() {
        let manager = AV1PolicyManager()
        let h264 = URL(string: "https://cdn.example.com/master_h264.m3u8")!

        // When only H.264 is provided
        let profile = manager.getPlaybackProfile(h264Master: h264, hevcMaster: nil, av1Master: nil)
        XCTAssertEqual(profile.codec, .h264)
        XCTAssertEqual(profile.selectedURL, h264)
        XCTAssertEqual(profile.reasonCode, "IOS_DEFAULT_H264")
    }
}
