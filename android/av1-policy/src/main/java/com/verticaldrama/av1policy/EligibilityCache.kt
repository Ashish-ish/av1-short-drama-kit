package com.verticaldrama.av1policy

import android.content.Context
import android.content.SharedPreferences
import android.os.Build

/**
 * Caches eligibility probe results, max AV1 rungs, and fallback cooldowns.
 * Keyed by device fingerprint, OS build, decoder name, and app version.
 */
class EligibilityCache(
    context: Context,
    private val appVersion: String = "1.0.0",
) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("av1_eligibility_cache", Context.MODE_PRIVATE)

    companion object {
        const val COOLDOWN_DURATION_MS = 7L * 24 * 60 * 60 * 1000 // 7 days
        const val ROLLING_WINDOW_MS = 24L * 60 * 60 * 1000 // 24 hours
    }

    private fun getCacheKeyPrefix(decoderName: String): String {
        val fingerprint = Build.FINGERPRINT.replace(":", "_")
        val buildId = Build.ID
        return "${fingerprint}__${buildId}__${decoderName}__${appVersion}"
    }

    enum class ProbeStatus {
        UNKNOWN,
        PASSED,
        FAILED
    }

    data class ProbeResult(
        val status: ProbeStatus,
        val decodeSpeedRatio: Float,
        val timestampMs: Long,
        val errorMessage: String? = null,
    )

    fun saveProbeResult(decoderName: String, rung: String, status: ProbeStatus, speedRatio: Float, error: String? = null) {
        val prefix = getCacheKeyPrefix(decoderName)
        prefs.edit()
            .putString("${prefix}__status__$rung", status.name)
            .putFloat("${prefix}__speed__$rung", speedRatio)
            .putLong("${prefix}__ts__$rung", System.currentTimeMillis())
            .putString("${prefix}__error__$rung", error ?: "")
            .apply()
    }

    fun getProbeResult(decoderName: String, rung: String): ProbeResult {
        val prefix = getCacheKeyPrefix(decoderName)
        val statusStr = prefs.getString("${prefix}__status__$rung", ProbeStatus.UNKNOWN.name) ?: ProbeStatus.UNKNOWN.name
        val status = try {
            ProbeStatus.valueOf(statusStr)
        } catch (e: Exception) {
            ProbeStatus.UNKNOWN
        }
        val speed = prefs.getFloat("${prefix}__speed__$rung", 0.0f)
        val ts = prefs.getLong("${prefix}__ts__$rung", 0L)
        val err = prefs.getString("${prefix}__error__$rung", null)

        return ProbeResult(status, speed, ts, if (err.isNullOrEmpty()) null else err)
    }

    fun getMaxAv1Rung(): String {
        return prefs.getString("cached_max_av1_rung", "720p") ?: "720p"
    }

    fun setMaxAv1Rung(rung: String) {
        prefs.edit().putString("cached_max_av1_rung", rung).apply()
    }

    fun recordFallback(reasonCode: String) {
        val now = System.currentTimeMillis()
        val countKey = "fallbacks_24h_count"
        val firstKey = "fallbacks_24h_first_ts"

        val firstTs = prefs.getLong(firstKey, 0L)
        var count = prefs.getInt(countKey, 0)

        if (now - firstTs > ROLLING_WINDOW_MS) {
            count = 1
            prefs.edit().putLong(firstKey, now).putInt(countKey, 1).apply()
        } else {
            count += 1
            prefs.edit().putInt(countKey, count).apply()
            if (count >= 3) {
                // Trigger 7-day cooldown
                prefs.edit().putLong("fallback_cooldown_until", now + COOLDOWN_DURATION_MS).apply()
            }
        }
    }

    fun isInFallbackCooldown(): Boolean {
        val until = prefs.getLong("fallback_cooldown_until", 0L)
        return System.currentTimeMillis() < until
    }

    fun clear() {
        prefs.edit().clear().apply()
    }
}
