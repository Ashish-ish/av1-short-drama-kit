package com.verticaldrama.av1policy;

import android.os.SystemClock;
import android.util.Log;
import androidx.media3.common.Player;
import androidx.media3.exoplayer.DecoderReuseEvaluation;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.exoplayer.analytics.AnalyticsListener;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Media3 AnalyticsListener capturing core vertical-drama benchmark metrics.
 */
public class Av1AnalyticsListener implements AnalyticsListener {

    private static final String TAG = "Av1AnalyticsListener";

    private final ExoPlayer player;
    private final Av1FallbackTracker fallbackTracker;
    public boolean isAv1Active;
    public String h264MasterUrl;

    private long prepareTimestampMs = 0L;
    private long decoderInitDurationMs = 0L;
    private long ttffMs = 0L;

    private long playbackStartTimestampMs = 0L;
    private long totalStallDurationMs = 0L;
    private long stallStartTimestampMs = 0L;

    private int totalRenderedFrames = 0;
    private int totalDroppedFrames = 0;

    public final List<Long> ttffHistory = new CopyOnWriteArrayList<>();
    public final List<Long> decoderInitHistory = new CopyOnWriteArrayList<>();

    public Av1AnalyticsListener(
            ExoPlayer player,
            Av1FallbackTracker fallbackTracker,
            boolean isAv1Active,
            String h264MasterUrl
    ) {
        this.player = player;
        this.fallbackTracker = fallbackTracker;
        this.isAv1Active = isAv1Active;
        this.h264MasterUrl = h264MasterUrl;
    }

    public Av1AnalyticsListener(ExoPlayer player, Av1FallbackTracker fallbackTracker) {
        this(player, fallbackTracker, true, "");
    }

    public void onPrepareStarted() {
        prepareTimestampMs = SystemClock.elapsedRealtime();
    }

    @Override
    public void onVideoDecoderInitialized(
            EventTime eventTime,
            String decoderName,
            long initializedTimestampMs,
            long initializationDurationMs
    ) {
        decoderInitDurationMs = initializationDurationMs;
        decoderInitHistory.add(initializationDurationMs);
        Log.d(TAG, "Video decoder initialized: " + decoderName + " in " + initializationDurationMs + "ms");
    }

    @Override
    public void onRenderedFirstFrame(
            EventTime eventTime,
            Object output,
            long renderTimeMs
    ) {
        if (prepareTimestampMs > 0) {
            ttffMs = SystemClock.elapsedRealtime() - prepareTimestampMs;
            ttffHistory.add(ttffMs);
            Log.d(TAG, "Rendered first frame. Time-To-First-Frame (TTFF): " + ttffMs + "ms");
        }
        playbackStartTimestampMs = SystemClock.elapsedRealtime();
    }

    @Override
    public void onDroppedVideoFrames(
            EventTime eventTime,
            int droppedFrames,
            long elapsedMs
    ) {
        totalDroppedFrames += droppedFrames;
        int renderedApprox = (int) (elapsedMs * 30 / 1000);
        totalRenderedFrames += renderedApprox;

        fallbackTracker.recordFrameMetrics(
                player,
                isAv1Active,
                h264MasterUrl,
                droppedFrames,
                renderedApprox
        );
    }

    @Override
    public void onPlaybackStateChanged(EventTime eventTime, int playbackState) {
        if (playbackState == Player.STATE_BUFFERING) {
            if (playbackStartTimestampMs > 0 && stallStartTimestampMs == 0L) {
                stallStartTimestampMs = SystemClock.elapsedRealtime();
            }
        } else if (playbackState == Player.STATE_READY) {
            if (stallStartTimestampMs > 0L) {
                totalStallDurationMs += (SystemClock.elapsedRealtime() - stallStartTimestampMs);
                stallStartTimestampMs = 0L;
            }
        }
    }

    public long getTtffMs() {
        return ttffMs;
    }

    public long getDecoderInitDurationMs() {
        return decoderInitDurationMs;
    }

    public int getTotalDroppedFrames() {
        return totalDroppedFrames;
    }
}
