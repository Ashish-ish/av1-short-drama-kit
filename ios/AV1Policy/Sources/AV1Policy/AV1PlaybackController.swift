import Foundation
import AVFoundation
import CoreMedia

public protocol AV1PlaybackControllerDelegate: AnyObject {
    func didTriggerFallback(toH264Master url: URL, resumeTime: CMTime, reason: String)
    func didUpdateMetrics(ttffSeconds: Double, droppedFrames: Int, stalls: Int)
}

/// AVPlayer controller with automatic seamless fallback to H.264
public class AV1PlaybackController: NSObject {

    public let player: AVPlayer
    public weak var delegate: AV1PlaybackControllerDelegate?

    public private(set) var activeProfile: PlaybackProfile?
    public private(set) var h264FallbackURL: URL?
    public private(set) var isFallbackActive: Bool = false

    private var timeObserverToken: Any?
    private var itemStatusObserver: NSKeyValueObservation?

    public override init() {
        self.player = AVPlayer()
        super.init()
        setupNotifications()
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
        itemStatusObserver?.invalidate()
        if let token = timeObserverToken {
            player.removeTimeObserver(token)
        }
    }

    private func setupNotifications() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleItemFailedNotification(_:)),
            name: .AVPlayerItemFailedToPlayToEndTime,
            object: nil
        )
    }

    /// Prepares and starts playback with the evaluated profile.
    public func loadVideo(
        h264Master: URL,
        hevcMaster: URL? = nil,
        av1Master: URL? = nil
    ) {
        self.h264FallbackURL = h264Master
        self.isFallbackActive = false

        let profile = AV1PolicyManager.shared.getPlaybackProfile(
            h264Master: h264Master,
            hevcMaster: hevcMaster,
            av1Master: av1Master
        )
        self.activeProfile = profile

        let asset = AVURLAsset(url: profile.selectedURL)
        let playerItem = AVPlayerItem(asset: asset)

        observePlayerItem(playerItem)
        player.replaceCurrentItem(with: playerItem)
        player.play()
    }

    private func observePlayerItem(_ item: AVPlayerItem) {
        itemStatusObserver?.invalidate()
        itemStatusObserver = item.observe(\.status, options: [.new, .old]) { [weak self] playerItem, _ in
            if playerItem.status == .failed {
                let error = playerItem.error
                self?.triggerFallback(reason: "PLAYER_ITEM_FAILED: \(error?.localizedDescription ?? "unknown")")
            }
        }
    }

    @objc private func handleItemFailedNotification(_ notification: Notification) {
        guard let item = notification.object as? AVPlayerItem, item == player.currentItem else { return }
        let error = notification.userInfo?[AVPlayerItemFailedToPlayToEndTimeErrorKey] as? Error
        triggerFallback(reason: "FAILED_TO_PLAY_TO_END: \(error?.localizedDescription ?? "unknown")")
    }

    /// Triggers mid-stream fallback to H.264 preserving current CMTime position
    public func triggerFallback(reason: String) {
        guard !isFallbackActive, let fallbackURL = h264FallbackURL else { return }
        isFallbackActive = true

        let currentPosition = player.currentTime()
        let fallbackItem = AVPlayerItem(url: fallbackURL)

        observePlayerItem(fallbackItem)
        player.replaceCurrentItem(with: fallbackItem)
        player.seek(to: currentPosition, toleranceBefore: .zero, toleranceAfter: .zero) { [weak self] _ in
            self?.player.play()
        }

        delegate?.didTriggerFallback(toH264Master: fallbackURL, resumeTime: currentPosition, reason: reason)
    }
}
