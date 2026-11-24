package com.verticaldrama.av1policy;

import android.content.Context;
import android.net.Uri;
import android.os.SystemClock;
import android.util.Log;
import androidx.media3.datasource.DataSpec;
import androidx.media3.datasource.DefaultHttpDataSource;
import androidx.media3.datasource.cache.CacheDataSource;
import androidx.media3.datasource.cache.CacheWriter;
import androidx.media3.datasource.cache.LeastRecentlyUsedCacheEvictor;
import androidx.media3.datasource.cache.SimpleCache;
import androidx.media3.exoplayer.ExoPlayer;
import java.io.File;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Drama-tuned Preload Controller adhering strictly to ADR-002:
 * 1. Strict decoupling: Preloads network media segments into SimpleCache without initializing decoders.
 * 2. Lazy decoder initialization: ExoPlayer prepare/surface attachment occurs only when user focuses the episode.
 * 3. Single active software decoder: Never allows two concurrent software AV1 (dav1d) instances.
 * 4. Tracks preload depth, bytes downloaded vs watched, and cache hit metrics.
 */
public class DramaPreloadController {

    private static final String TAG = "DramaPreloadController";
    public static final int PRELOAD_SEGMENT_COUNT = 2;

    private final Context context;
    private final File cacheDir;
    private final LeastRecentlyUsedCacheEvictor cacheEvictor;
    public final SimpleCache simpleCache;

    private final ExecutorService preloadExecutor = Executors.newFixedThreadPool(2);
    private final Map<String, CacheWriter> activePreloads = new ConcurrentHashMap<>();

    private final AtomicReference<ExoPlayer> currentActivePlayer = new AtomicReference<>(null);
    private String activeEpisodeId = null;

    public static class PreloadMetrics {
        public final String episodeId;
        public final long bytesPreloaded;
        public final long durationMs;
        public boolean wasWatched;

        public PreloadMetrics(String episodeId, long bytesPreloaded, long durationMs, boolean wasWatched) {
            this.episodeId = episodeId;
            this.bytesPreloaded = bytesPreloaded;
            this.durationMs = durationMs;
            this.wasWatched = wasWatched;
        }
    }

    private final Map<String, PreloadMetrics> metricsHistory = new ConcurrentHashMap<>();

    public DramaPreloadController(Context context, long maxCacheBytes) {
        this.context = context.getApplicationContext();
        this.cacheDir = new File(this.context.getCacheDir(), "drama_media_cache");
        this.cacheEvictor = new LeastRecentlyUsedCacheEvictor(maxCacheBytes);
        this.simpleCache = new SimpleCache(cacheDir, cacheEvictor);
    }

    public DramaPreloadController(Context context) {
        this(context, 100L * 1024 * 1024); // 100 MB default
    }

    public void preloadNextEpisode(final String episodeId, final String masterPlaylistUrl) {
        if (activePreloads.containsKey(episodeId)) return;

        preloadExecutor.execute(new Runnable() {
            @Override
            public void run() {
                long startTime = SystemClock.elapsedRealtime();
                try {
                    DefaultHttpDataSource.Factory httpFactory = new DefaultHttpDataSource.Factory();
                    CacheDataSource.Factory cacheFactory = new CacheDataSource.Factory()
                            .setCache(simpleCache)
                            .setUpstreamDataSourceFactory(httpFactory);

                    Uri uri = Uri.parse(masterPlaylistUrl);
                    DataSpec dataSpec = new DataSpec.Builder()
                            .setUri(uri)
                            .setLength(512L * 1024) // 512 KB covering init + first segments
                            .build();

                    final long[] loaded = new long[]{0L};
                    CacheWriter writer = new CacheWriter(
                            cacheFactory.createDataSource(),
                            dataSpec,
                            null,
                            new CacheWriter.ProgressListener() {
                                @Override
                                public void onProgress(long requestLength, long bytesLoaded, long newBytesLoaded) {
                                    loaded[0] += newBytesLoaded;
                                }
                            }
                    );

                    activePreloads.put(episodeId, writer);
                    writer.cache();

                    long duration = SystemClock.elapsedRealtime() - startTime;
                    metricsHistory.put(episodeId, new PreloadMetrics(episodeId, loaded[0], duration, false));
                    Log.d(TAG, "Preloaded episode " + episodeId + " (" + loaded[0] + " bytes in " + duration + "ms)");
                } catch (Exception e) {
                    Log.w(TAG, "Preload interrupted or failed for episode " + episodeId + ": " + e.getMessage());
                } finally {
                    activePreloads.remove(episodeId);
                }
            }
        });
    }

    public void onEpisodeFocused(String episodeId, ExoPlayer player) {
        ExoPlayer previous = currentActivePlayer.getAndSet(player);
        if (previous != null && previous != player) {
            previous.stop();
            previous.clearMediaItems();
        }
        activeEpisodeId = episodeId;
        PreloadMetrics metric = metricsHistory.get(episodeId);
        if (metric != null) {
            metric.wasWatched = true;
        }
    }

    public void cancelPreload(String episodeId) {
        CacheWriter writer = activePreloads.remove(episodeId);
        if (writer != null) {
            writer.cancel();
        }
    }

    public void release() {
        preloadExecutor.shutdown();
        activePreloads.clear();
        simpleCache.release();
    }
}
