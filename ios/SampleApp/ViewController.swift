import UIKit
import AVFoundation
import AV1Policy

class ViewController: UIViewController, AV1PlaybackControllerDelegate {

    private let playbackController = AV1PlaybackController()
    private var playerLayer: AVPlayerLayer?

    private let codecBadge = UILabel()
    private let statusLabel = UILabel()
    private let fallbackButton = UIButton(type: .system)

    // Master playlists
    private let h264Master = URL(string: "https://cdn.example.com/drama/ep01/master_h264.m3u8")!
    private let hevcMaster = URL(string: "https://cdn.example.com/drama/ep01/master_hevc.m3u8")!
    private let av1Master = URL(string: "https://cdn.example.com/drama/ep01/master_av1.m3u8")!

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black

        setupPlayerUI()
        playbackController.delegate = self

        // Start playback with hardware-only policy
        playbackController.loadVideo(
            h264Master: h264Master,
            hevcMaster: hevcMaster,
            av1Master: av1Master
        )

        updateHUD()
    }

    private func setupPlayerUI() {
        let layer = AVPlayerLayer(player: playbackController.player)
        layer.frame = view.bounds
        layer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(layer)
        self.playerLayer = layer

        // Overlay HUD
        codecBadge.frame = CGRect(x: 20, y: 60, width: 300, height: 28)
        codecBadge.textColor = .systemGreen
        codecBadge.font = .boldSystemFont(ofSize: 14)
        view.addSubview(codecBadge)

        statusLabel.frame = CGRect(x: 20, y: 92, width: 340, height: 40)
        statusLabel.textColor = .lightGray
        statusLabel.font = .systemFont(ofSize: 12)
        statusLabel.numberOfLines = 2
        view.addSubview(statusLabel)

        fallbackButton.frame = CGRect(x: 20, y: 140, width: 220, height: 36)
        fallbackButton.setTitle("⚡ Force Fallback to H.264", for: .normal)
        fallbackButton.setTitleColor(.white, for: .normal)
        fallbackButton.backgroundColor = .systemRed
        fallbackButton.layer.cornerRadius = 6
        fallbackButton.addTarget(self, action: #selector(didTapForceFallback), for: .touchUpInside)
        view.addSubview(fallbackButton)
    }

    @objc private func didTapForceFallback() {
        playbackController.triggerFallback(reason: "MANUAL_DEBUG_FORCE_FALLBACK")
    }

    private func updateHUD() {
        if let profile = playbackController.activeProfile {
            codecBadge.text = "Active Codec: \(profile.codec.rawValue.uppercased()) (HW Decode: \(profile.isHardwareDecode))"
            statusLabel.text = "Policy: \(profile.reasonCode)\nMaster: \(profile.selectedURL.lastPathComponent)"
        }
    }

    // MARK: - AV1PlaybackControllerDelegate

    func didTriggerFallback(toH264Master url: URL, resumeTime: CMTime, reason: String) {
        let sec = CMTimeGetSeconds(resumeTime)
        codecBadge.text = "Active Codec: H.264 (FALLBACK ACTIVE)"
        codecBadge.textColor = .systemRed
        statusLabel.text = "Fallback Triggered: \(reason)\nResumed @ \(String(format: "%.2f", sec))s"
    }

    func didUpdateMetrics(ttffSeconds: Double, droppedFrames: Int, stalls: Int) {
        // Report to analytics
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        playerLayer?.frame = view.bounds
    }
}
