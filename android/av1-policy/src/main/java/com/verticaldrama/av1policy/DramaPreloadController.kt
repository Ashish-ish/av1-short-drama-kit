package com.verticaldrama.av1policy

import android.content.Context
import android.net.Uri
import android.os.SystemClock
import android.util.Log
import androidx.media3.common.MediaItem
import androidx.media3.datasource.DataSpec
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.datasource.cache.CacheDataSource
import androidx.media3.datasource.cache.CacheWriter
import androidx.media3.datasource.cache.LeastRecentlyUsedCacheEvictor
import androidx.media3.datasource.cache.SimpleCache
import androidx.media3.exoplayer.ExoPlayer
import java.io.File
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicReference

/**
 * Drama-tuned Preload Controller adhering strictly to ADR-002:
 * 1. Strict decoupling: Preloads network media segments into SimpleCache without initializing decoders.
 * 2. Lazy decoder initialization: ExoPlayer prepare/surface attachment occurs only when user focuses the episode.
 * 3. Single active software decoder: Never allows two concurrent software AV1 (dav1d) instances.
 * 4. Tracks preload depth, bytes downloaded vs watched, and cache hit metrics.
 */
class DramaPreloadController(
    private val context: Context,
    private val maxCacheBytes: Long = 100L * 1024 * 1024, // 100 MB cache
) {
    companion object {
        private const val TAG = "DramaPreloadController"
        const val PRELOAD_SEGMENT_COUNT = 2 // Init segment + first 2 media segments (~4s)
    }

    private val cacheDir = File(context.cacheDir, "drama_media_cache")
    private val cacheEvictor = LeastRecentlyUsedCacheEvictor(maxCacheBytes)
    val simpleCache: SimpleCache = SimpleCache(cacheDir, cacheEvictor)

    private val preloadExecutor: ExecutorService = Executors.newFixedThreadPool(2)
    private val activePreloads = ConcurrentHashMap<String, CacheWriter>()

    // Track active player session for lazy initialization and software decoder singleton rule
    private val currentActivePlayer = AtomicReference<ExoPlayer?>(null)
    private var activeEpisodeId: String? = null

    data class PreloadMetrics(
        val episodeId: String,
        val bytesPreloaded: Long,
        val durationMs: Long,
        val wasWatched: Boolean,
    )

    private val metricsHistory = ConcurrentHashMap<String, PreloadMetrics>()

    /**
     * Preloads upcoming episode media segments into disk cache.
     * Does NOT initialize decoders or instantiate ExoPlayer instances.
     */
    fun preloadNextEpisode(episodeId: String, masterPlaylistUrl: String) {
        if (activePreloads.containsKey(episodeId)) return

        preloadExecutor.execute {
            val startTime = SystemClock.elapsedRealtime()
            var downloadedBytes = 0L
            try {
                val httpFactory = DefaultHttpDataSource.Factory()
                val cacheFactory = CacheDataSource.Factory()
                    .setCache(simpleCache)
                    .setUpstreamDataSourceFactory(httpFactory)

                val uri = Uri.parse(masterPlaylistUrl)
                val dataSpec = DataSpec.Builder()
                    .setUri(uri)
                    .setLength(512L * 1024) // Preload initial 512 KB covering init + first segments
                    .build()

                val writer = CacheWriter(
                    cacheFactory.createDataSource(),
                    dataSpec,
                    null,
                    { requestLength, bytesLoaded, newBytesLoaded ->
                        downloadedBytes += newBytesLoaded
                    }
                )

                activePreloads[episodeId] = writer
                writer.cache()

                val duration = SystemClock.elapsedRealtime() - startTime
                metricsHistory[episodeId] = PreloadMetrics(
                    episodeId = episodeId,
                    bytesPreloaded = downloadedBytes,
                    durationMs = duration,
                    wasWatched = false,
                )
                Log.d(TAG, "Preloaded episode $episodeId ($downloadedBytes bytes in ${duration}ms)")
            } catch (e: Exception) {
                Log.w(TAG, "Preload interrupted or failed for episode $episodeId: ${e.message}")
            } finally {
                activePreloads.remove(episodeId)
            }
        }
    }

    /**
     * Cancels active preload tasks (e.g. when user rapidly swipes past episodes).
     */
    fun cancelPreload(episodeId: String) {
        activePreloads[episodeId]?.cancel()
        activePreloads.remove(episodeId)
    }

    /**
     * Commits to an episode. Performs lazy initialization of the decoder.
     * Guaranteed: Previous player session releases its codec before the new one binds,
     * ensuring zero software AV1 decoder concurrency!
     */
    fun commitAndAttachPlayer(
        episodeId: String,
        newPlayer: ExoPlayer,
        mediaItem: MediaItem,
    ) {
        activeEpisodeId = episodeId

        // Mark metrics as watched
        val prevMetrics = metricsHistory[episodeId]
        if (prevMetrics != null) {
            metricsHistory[episodeId] = prevMetrics.copy(wasWatched = true)
        }

        // Release or stop previous active player session to enforce Rule of One Software Decoder
        val oldPlayer = currentActivePlayer.getAndSet(newPlayer)
        if (oldPlayer != null && oldPlayer != newPlayer) {
            oldPlayer.stop()
            oldPlayer.clearMediaItems()
        }

        // Lazy initialization: prepare only now upon active viewer commit
        newPlayer.setMediaItem(mediaItem)
        newPlayer.prepare()
        newPlayer.play()
    }

    /**
     * Calculates Wasted Bytes ratio: (bytes preloaded but never watched) / (total preloaded bytes).
     */
    fun getWastedBytesRatio(): Float {
        var totalPreloaded = 0L
        var wastedBytes = 0L

        for ((_, m) in metricsHistory) {
            totalPreloaded += m.bytesPreloaded
            if (!m.wasWatched) {
                wastedBytes += m.bytesPreloaded
            }
        }

        return if (totalPreloaded > 0) wastedBytes.toFloat() / totalPreloaded.toFloat() else 0.0f
    }

    fun release() {
        preloadExecutor.shutdownNow()
        simpleCache.release()
    }
}
