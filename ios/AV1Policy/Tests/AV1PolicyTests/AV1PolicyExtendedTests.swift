import XCTest
@testable import AV1Policy

final class AV1PolicyExtendedTests: XCTestCase {

    func testCodecEnumValues() {
        XCTAssertEqual(PlaybackCodec.h264.rawValue, "h264")
        XCTAssertEqual(PlaybackCodec.hevc.rawValue, "hevc")
        XCTAssertEqual(PlaybackCodec.av1.rawValue, "av1")
    }

    func testProfileInitialization() {
        let dummyURL = URL(string: "https://cdn.example.com/test.m3u8")!
        let profile = PlaybackProfile(
            selectedURL: dummyURL,
            codec: .av1,
            maxRung: "540p",
            isHardwareDecode: true,
            reasonCode: "TEST_REASON"
        )

        XCTAssertEqual(profile.selectedURL, dummyURL)
        XCTAssertEqual(profile.codec, .av1)
        XCTAssertEqual(profile.maxRung, "540p")
        XCTAssertTrue(profile.isHardwareDecode)
        XCTAssertEqual(profile.reasonCode, "TEST_REASON")
    }
}
