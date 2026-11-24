package com.verticaldrama.sample

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.exoplayer.DefaultRenderersFactory
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.verticaldrama.av1policy.Av1AnalyticsListener
import com.verticaldrama.av1policy.Av1FallbackTracker
import com.verticaldrama.av1policy.Av1MediaCodecSelector
import com.verticaldrama.av1policy.DramaPreloadController
import com.verticaldrama.av1policy.PlaybackPolicyManager

class MainActivity : AppCompatActivity(), Av1FallbackTracker.FallbackListener {

    private lateinit var playerView: PlayerView
    private lateinit var tvCodecInfo: TextView
    private lateinit var tvMetrics: TextView
    private lateinit var tvPolicyReason: TextView
    private lateinit var btnForceError: Button

    private lateinit var policyManager: PlaybackPolicyManager
    private lateinit var preloadController: DramaPreloadController
    private var player: ExoPlayer? = null
    private var analyticsListener: Av1AnalyticsListener? = null

    private val updateHandler = Handler(Looper.getMainLooper())
    private var isFallbackActive = false

    // Sample multi-codec ladder endpoints (pointing to local or CDN fMP4 HLS)
    private val masterH264 = "https://cdn.example.com/drama/ep01/master_h264.m3u8"
    private val masterHevc = "https://cdn.example.com/drama/ep01/master_hevc.m3u8"
    private val masterAv1 = "https://cdn.example.com/drama/ep01/master_av1.m3u8"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        playerView = findViewById(R.id.playerView)
        tvCodecInfo = findViewById(R.id.tvCodecInfo)
        tvMetrics = findViewById(R.id.tvMetrics)
        tvPolicyReason = findViewById(R.id.tvPolicyReason)
        btnForceError = findViewById(R.id.btnForceError)

        policyManager = PlaybackPolicyManager(this)
        preloadController = DramaPreloadController(this)
        policyManager.fallbackTracker.fallbackListener = this

        btnForceError.setOnClickListener {
            // Simulate a catastrophic decoder failure to demonstrate guaranteed H.264 fallback
            player?.let { p ->
                val dummyError = PlaybackException(
                    "Simulated decoder error for fallback demonstration",
                    null,
                    PlaybackException.ERROR_CODE_DECODER_INIT_FAILED
                )
                policyManager.fallbackTracker.handlePlaybackError(
                    player = p,
                    isAv1Active = true,
                    h264MasterUrl = masterH264,
                    error = dummyError
                )
            }
        }

        initializePlayer()
        startMetricsUpdater()
    }

    private fun initializePlayer() {
        // Query policy manager for optimal master stream
        val profile = policyManager.getPlaybackProfile(
            h264MasterUrl = masterH264,
            hevcMasterUrl = masterHevc,
            av1MasterUrl = masterAv1,
            hasDrm = false
        )

        tvCodecInfo.text = "Active Codec: ${profile.selectedCodec.uppercase()} (Max Rung: ${profile.maxRung})"
        tvPolicyReason.text = "Policy: ${profile.reasonCode}"

        // Build ExoPlayer with custom Av1MediaCodecSelector
        val renderersFactory = DefaultRenderersFactory(this).apply {
            setMediaCodecSelector(Av1MediaCodecSelector(policyManager))
        }

        val exo = ExoPlayer.Builder(this, renderersFactory).build()
        player = exo
        playerView.player = exo

        analyticsListener = Av1AnalyticsListener(
            player = exo,
            fallbackTracker = policyManager.fallbackTracker,
            isAv1Active = profile.isAv1Active,
            h264MasterUrl = masterH264,
        )
        exo.addAnalyticsListener(analyticsListener!!)

        val mediaItem = MediaItem.fromUri(profile.selectedMasterUrl)

        // Lazy initialization via DramaPreloadController
        analyticsListener?.onPrepareStarted()
        preloadController.commitAndAttachPlayer(
            episodeId = "ep01",
            newPlayer = exo,
            mediaItem = mediaItem
        )

        // Preload next episode data asynchronously
        preloadController.preloadNextEpisode("ep02", profile.selectedMasterUrl)
    }

    override fun onFallbackTriggered(
        h264MasterUrl: String,
        resumePositionMs: Long,
        reasonCode: String,
    ) {
        runOnUiThread {
            isFallbackActive = true
            tvCodecInfo.text = "Active Codec: H.264 (FALLBACK ACTIVE)"
            tvCodecInfo.setTextColor(0xFFEF4444.toInt()) // Red
            tvPolicyReason.text = "Fallback Triggered: $reasonCode | Resuming @ ${resumePositionMs}ms"

            player?.let { p ->
                val fallbackItem = MediaItem.fromUri(h264MasterUrl)
                p.setMediaItem(fallbackItem, resumePositionMs)
                p.prepare()
                p.play()
            }
        }
    }

    private fun startMetricsUpdater() {
        updateHandler.postDelayed(object : Runnable {
            override fun run() {
                analyticsListener?.let { a ->
                    val summary = a.getMetricsSummary()
                    val ttff = summary["ttff_ms"]
                    val initLat = summary["decoder_init_duration_ms"]
                    val dropped = summary["total_dropped_frames"]
                    val dropPerMin = summary["dropped_frames_per_minute"]
                    tvMetrics.text = "TTFF: ${ttff}ms | Decoder Init: ${initLat}ms | Dropped: $dropped ($dropPerMin/min)"
                }
                updateHandler.postDelayed(this, 1000)
            }
        }, 1000)
    }

    override fun onDestroy() {
        super.onDestroy()
        updateHandler.removeCallbacksAndMessages(null)
        player?.release()
        preloadController.release()
    }
}
