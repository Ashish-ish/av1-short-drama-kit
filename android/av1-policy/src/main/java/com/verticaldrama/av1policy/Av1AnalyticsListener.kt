package com.verticaldrama.av1policy

import android.os.SystemClock
import android.util.Log
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.DecoderReuseEvaluation
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.analytics.AnalyticsListener
import java.util.concurrent.CopyOnWriteArrayList

/**
 * Media3 AnalyticsListener capturing core vertical-drama benchmark metrics:
 * - Time to first frame (TTFF)
 * - Decoder initialization time
 * - Dropped frames per minute
 * - Rebuffer ratio (stall duration / total watch time)
 * - Mid-stream fallback events
 */
class Av1AnalyticsListener(
    private val player: ExoPlayer,
    private val fallbackTracker: Av1FallbackTracker,
    var isAv1Active: Boolean = true,
    var h264MasterUrl: String = "",
) : AnalyticsListener {

    companion object {
        private const val TAG = "Av1AnalyticsListener"
    }

    private var prepareTimestampMs: Long = 0L
    private var decoderInitTimestampMs: Long = 0L
    private var decoderInitDurationMs: Long = 0L
    private var ttffMs: Long = 0L

    private var playbackStartTimestampMs: Long = 0L
    private var totalWatchDurationMs: Long = 0L
    private var totalStallDurationMs: Long = 0L
    private var stallStartTimestampMs: Long = 0L

    private var totalRenderedFrames = 0
    private var totalDroppedFrames = 0

    val ttffHistory = CopyOnWriteArrayList<Long>()
    val decoderInitHistory = CopyOnWriteArrayList<Long>()

    fun onPrepareStarted() {
        prepareTimestampMs = SystemClock.elapsedRealtime()
    }

    override fun onVideoDecoderInitialized(
        eventTime: AnalyticsListener.EventTime,
        decoderName: String,
        initializedTimestampMs: Long,
        initializationDurationMs: Long,
    ) {
        decoderInitDurationMs = initializationDurationMs
        decoderInitHistory.add(initializationDurationMs)
        Log.d(TAG, "Video decoder initialized: $decoderName in ${initializationDurationMs}ms")
    }

    override fun onRenderedFirstFrame(
        eventTime: AnalyticsListener.EventTime,
        output: Any,
        renderTimeMs: Long,
    ) {
        if (prepareTimestampMs > 0) {
            ttffMs = SystemClock.elapsedRealtime() - prepareTimestampMs
            ttffHistory.add(ttffMs)
            Log.d(TAG, "Rendered first frame. Time-To-First-Frame (TTFF): ${ttffMs}ms")
        }
        playbackStartTimestampMs = SystemClock.elapsedRealtime()
    }

    override fun onDroppedVideoFrames(
        eventTime: AnalyticsListener.EventTime,
        droppedFrames: Int,
        elapsedMs: Long,
    ) {
        totalDroppedFrames += droppedFrames
        // Approximate rendered frames in elapsed interval (~30 fps)
        val renderedApprox = (elapsedMs * 30 / 1000).toInt()
        totalRenderedFrames += renderedApprox

        fallbackTracker.recordFrameMetrics(
            player = player,
            isAv1Active = isAv1Active,
            h264MasterUrl = h264MasterUrl,
            droppedFrames = droppedFrames,
            renderedFrames = renderedApprox,
        )
    }

    override fun onPlaybackStateChanged(
        eventTime: AnalyticsListener.EventTime,
        playbackState: Int,
    ) {
        when (playbackState) {
            Player.STATE_BUFFERING -> {
                if (playbackStartTimestampMs > 0 && stallStartTimestampMs == 0L) {
                    stallStartTimestampMs = SystemClock.elapsedRealtime()
                }
            }
            Player.STATE_READY -> {
                if (stallStartTimestampMs > 0L) {
                    val stallMs = SystemClock.elapsedRealtime() - stallStartTimestampMs
                    totalStallDurationMs += stallMs
                    stallStartTimestampMs = 0L
                    Log.d(TAG, "Rebuffer stall ended. Duration: ${stallMs}ms")
                }
            }
            Player.STATE_ENDED -> {
                if (playbackStartTimestampMs > 0) {
                    totalWatchDurationMs += (SystemClock.elapsedRealtime() - playbackStartTimestampMs)
                }
            }
        }
    }

    override fun onPlayerError(
        eventTime: AnalyticsListener.EventTime,
        error: PlaybackException,
    ) {
        fallbackTracker.handlePlaybackError(
            player = player,
            isAv1Active = isAv1Active,
            h264MasterUrl = h264MasterUrl,
            error = error,
        )
    }

    fun getMetricsSummary(): Map<String, Any> {
        val watchSec = (totalWatchDurationMs / 1000.0).coerceAtLeast(0.1)
        val droppedPerMin = (totalDroppedFrames / watchSec) * 60.0
        val rebufferRatio = if (totalWatchDurationMs > 0) totalStallDurationMs.toDouble() / totalWatchDurationMs.toDouble() else 0.0

        return mapOf(
            "ttff_ms" to ttffMs,
            "decoder_init_duration_ms" to decoderInitDurationMs,
            "total_dropped_frames" to totalDroppedFrames,
            "dropped_frames_per_minute" to roundToTwo(droppedPerMin),
            "rebuffer_ratio" to roundToTwo(rebufferRatio),
            "total_watch_seconds" to roundToTwo(watchSec),
            "total_stall_ms" to totalStallDurationMs,
        )
    }

    private fun roundToTwo(v: Double): Double = Math.round(v * 100.0) / 100.0
}
