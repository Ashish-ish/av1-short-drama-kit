import Foundation
import AVFoundation

/// Collects performance and diagnostic metrics from AVPlayerItemAccessLog and AVPlayerItemErrorLog
public class AV1MetricsCollector {

    public struct MetricsSummary {
        public let startupTimeSeconds: Double
        public let totalDroppedFrames: Int
        public let numberOfStalls: Int
        public let indicatedBitrate: Double
        public let observedBitrate: Double
    }

    public static func inspectMetrics(for playerItem: AVPlayerItem?) -> MetricsSummary? {
        guard let item = playerItem, let accessLog = item.accessLog() else { return nil }

        var startupTime: Double = 0.0
        var droppedFrames = 0
        var stalls = 0
        var indicatedBitrate: Double = 0.0
        var observedBitrate: Double = 0.0

        for event in accessLog.events {
            if event.startupTime > 0 && startupTime == 0.0 {
                startupTime = event.startupTime
            }
            droppedFrames += event.numberOfDroppedVideoFrames
            stalls += event.numberOfStalls
            indicatedBitrate = max(indicatedBitrate, event.indicatedBitrate)
            observedBitrate = max(observedBitrate, event.observedBitrate)
        }

        return MetricsSummary(
            startupTimeSeconds: startupTime,
            totalDroppedFrames: droppedFrames,
            numberOfStalls: stalls,
            indicatedBitrate: indicatedBitrate,
            observedBitrate: observedBitrate
        )
    }
}
