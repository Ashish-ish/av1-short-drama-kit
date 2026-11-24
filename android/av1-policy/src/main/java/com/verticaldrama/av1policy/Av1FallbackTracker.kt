package com.verticaldrama.av1policy

import android.os.SystemClock
import android.util.Log
import androidx.media3.common.PlaybackException
import androidx.media3.exoplayer.ExoPlayer
import java.util.LinkedList

/**
 * Monitors real-time playback health for AV1 streams:
 * - Tracks dropped frames over a 10-second sliding window
 * - Detects decoder initialization and fatal decode exceptions
 * - Triggers mid-stream fallback to H.264 master while preserving PTS
 * - Enforces the 3-fallback penalty (7-day cooldown)
 */
class Av1FallbackTracker(
    private val policyManager: PlaybackPolicyManager,
    private val cache: EligibilityCache,
) {
    companion object {
        private const val TAG = "Av1FallbackTracker"
        const val SLIDING_WINDOW_MS = 10_000L // 10 seconds
        const val MAX_DROPPED_FRAME_PCT = 5.0f // Fallback threshold: 5% dropped frames
    }

    private data class FrameDropSample(val timestampMs: Long, val droppedFrames: Int, val renderedFrames: Int)

    private val samples = LinkedList<FrameDropSample>()

    interface FallbackListener {
        fun onFallbackTriggered(
            h264MasterUrl: String,
            resumePositionMs: Long,
            reasonCode: String,
        )
    }

    var fallbackListener: FallbackListener? = null

    /**
     * Records rendered and dropped frame counts from AnalyticsListener.
     */
    fun recordFrameMetrics(
        player: ExoPlayer,
        isAv1Active: Boolean,
        h264MasterUrl: String,
        droppedFrames: Int,
        renderedFrames: Int,
    ) {
        if (!isAv1Active) return

        val now = SystemClock.elapsedRealtime()
        samples.addLast(FrameDropSample(now, droppedFrames, renderedFrames))

        // Purge samples older than 10 seconds
        while (samples.isNotEmpty() && (now - samples.first.timestampMs > SLIDING_WINDOW_MS)) {
            samples.removeFirst()
        }

        var totalDropped = 0
        var totalRendered = 0
        for (s in samples) {
            totalDropped += s.droppedFrames
            totalRendered += s.renderedFrames
        }

        val totalExpected = totalDropped + totalRendered
        if (totalExpected >= 60) { // Evaluate after at least ~2 seconds of frames
            val dropPct = (totalDropped.toFloat() / totalExpected.toFloat()) * 100.0f
            if (dropPct > MAX_DROPPED_FRAME_PCT) {
                Log.w(TAG, "Sustained frame drops exceeded threshold: ${dropPct}% over 10s. Triggering fallback to H.264.")
                triggerFallback(
                    player = player,
                    h264MasterUrl = h264MasterUrl,
                    reasonCode = "HIGH_DROPPED_FRAMES_${dropPct.toInt()}_PCT",
                    lowerMaxRung = true,
                )
            }
        }
    }

    /**
     * Handles playback errors or decoder initialization failures.
     */
    fun handlePlaybackError(
        player: ExoPlayer,
        isAv1Active: Boolean,
        h264MasterUrl: String,
        error: PlaybackException,
    ) {
        if (!isAv1Active) return

        val isDecoderError = error.errorCode == PlaybackException.ERROR_CODE_DECODER_INIT_FAILED ||
                error.errorCode == PlaybackException.ERROR_CODE_DECODING_FAILED

        val reasonCode = if (isDecoderError) "DECODER_FAILURE_${error.errorCodeName}" else "PLAYBACK_ERROR_${error.errorCodeName}"
        Log.e(TAG, "AV1 Playback error encountered: $reasonCode. Executing immediate fallback to H.264.", error)

        triggerFallback(
            player = player,
            h264MasterUrl = h264MasterUrl,
            reasonCode = reasonCode,
            lowerMaxRung = false,
        )
    }

    private fun triggerFallback(
        player: ExoPlayer,
        h264MasterUrl: String,
        reasonCode: String,
        lowerMaxRung: Boolean,
    ) {
        val currentPositionMs = player.currentPosition
        cache.recordFallback(reasonCode)

        if (lowerMaxRung) {
            val currentMax = cache.getMaxAv1Rung()
            val nextMax = when (currentMax) {
                "720p" -> "540p"
                "540p" -> "360p"
                else -> "none"
            }
            cache.setMaxAv1Rung(nextMax)
            Log.i(TAG, "Lowered device max AV1 rung from $currentMax to $nextMax")
        }

        samples.clear()
        fallbackListener?.onFallbackTriggered(h264MasterUrl, currentPositionMs, reasonCode)
    }
}
