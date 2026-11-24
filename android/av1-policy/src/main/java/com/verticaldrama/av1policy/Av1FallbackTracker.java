package com.verticaldrama.av1policy;

import android.os.SystemClock;
import android.util.Log;
import androidx.media3.common.MediaItem;
import androidx.media3.exoplayer.ExoPlayer;

/**
 * Tracks dropped frames and decode failures during playback.
 * If dropped frames exceed 5% or unrecoverable decoder stalls occur,
 * automatically triggers seamless fallback to the H.264 ladder per ADR-004.
 */
public class Av1FallbackTracker {

    private static final String TAG = "Av1FallbackTracker";
    private static final double MAX_DROP_RATIO = 0.05; // 5% drop threshold

    private final PlaybackPolicyManager policyManager;
    private final EligibilityCache cache;

    public interface FallbackListener {
        void onFallbackTriggered(String reason, long resumePositionMs);
    }

    private FallbackListener listener;

    public Av1FallbackTracker(PlaybackPolicyManager policyManager, EligibilityCache cache) {
        this.policyManager = policyManager;
        this.cache = cache;
    }

    public void setFallbackListener(FallbackListener listener) {
        this.listener = listener;
    }

    public void recordFrameMetrics(
            ExoPlayer player,
            boolean isAv1Active,
            String h264MasterUrl,
            int droppedFrames,
            int renderedFrames
    ) {
        if (!isAv1Active) return;

        int total = droppedFrames + renderedFrames;
        if (total >= 30) { // Evaluate after at least 1s of content
            double dropRatio = (double) droppedFrames / (double) total;
            if (dropRatio > MAX_DROP_RATIO) {
                Log.w(TAG, "Frame drop ratio exceeded threshold (" + (dropRatio * 100) + "%). Triggering fallback.");
                triggerFallback(player, h264MasterUrl, "EXCESSIVE_FRAME_DROPS");
            }
        }
    }

    public void triggerFallback(ExoPlayer player, String h264MasterUrl, String reason) {
        cache.recordFallbackEvent();

        long currentPositionMs = player.getCurrentPosition();
        boolean playWhenReady = player.getPlayWhenReady();

        Log.i(TAG, "Triggering runtime fallback to H.264 @ " + currentPositionMs + "ms. Reason: " + reason);

        MediaItem h264Item = MediaItem.fromUri(h264MasterUrl);
        player.setMediaItem(h264Item, currentPositionMs);
        player.prepare();
        player.setPlayWhenReady(playWhenReady);

        if (listener != null) {
            listener.onFallbackTriggered(reason, currentPositionMs);
        }
    }
}
