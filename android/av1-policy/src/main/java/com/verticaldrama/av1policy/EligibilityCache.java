package com.verticaldrama.av1policy;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Persists eligibility probe results, maximum allowed rungs, and mid-stream
 * fallback history per ADR-004.
 */
public class EligibilityCache {

    private static final String PREF_NAME = "av1_playback_policy_cache";
    private static final String KEY_APP_VERSION = "cached_app_version";
    private static final String KEY_FALLBACK_COUNT = "fallback_count_24h";
    private static final String KEY_LAST_FALLBACK_TS = "last_fallback_ts";
    private static final String KEY_MAX_RUNG = "max_av1_rung";
    private static final String KEY_PROBE_PREFIX = "probe_result_";

    private static final long COOLDOWN_DURATION_MS = 7L * 24 * 60 * 60 * 1000L; // 7 days per ADR-004
    private static final int MAX_FALLBACKS_PER_WINDOW = 3;

    public enum ProbeStatus {
        UNKNOWN,
        PASSED,
        FAILED,
        EXPIRED
    }

    public static class ProbeResult {
        public final ProbeStatus status;
        public final double decodeSpeedRatio;
        public final long timestampMs;

        public ProbeResult(ProbeStatus status, double decodeSpeedRatio, long timestampMs) {
            this.status = status;
            this.decodeSpeedRatio = decodeSpeedRatio;
            this.timestampMs = timestampMs;
        }
    }

    private final SharedPreferences prefs;

    public EligibilityCache(Context context, String appVersion) {
        this.prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        checkVersionInvalidation(appVersion);
    }

    private void checkVersionInvalidation(String appVersion) {
        String cachedVersion = prefs.getString(KEY_APP_VERSION, null);
        if (cachedVersion == null || !cachedVersion.equals(appVersion)) {
            prefs.edit()
                    .clear()
                    .putString(KEY_APP_VERSION, appVersion)
                    .putString(KEY_MAX_RUNG, "540p")
                    .apply();
        }
    }

    public void saveProbeResult(String decoderName, String rung, ProbeStatus status, double speedRatio) {
        JSONObject json = new JSONObject();
        try {
            json.put("status", status.name());
            json.put("speedRatio", speedRatio);
            json.put("timestamp", System.currentTimeMillis());
            prefs.edit().putString(KEY_PROBE_PREFIX + decoderName + "_" + rung, json.toString()).apply();
        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    public ProbeResult getProbeResult(String decoderName, String rung) {
        String raw = prefs.getString(KEY_PROBE_PREFIX + decoderName + "_" + rung, null);
        if (raw == null) {
            return new ProbeResult(ProbeStatus.UNKNOWN, 0.0, 0L);
        }
        try {
            JSONObject json = new JSONObject(raw);
            long ts = json.optLong("timestamp", 0L);
            if (System.currentTimeMillis() - ts > COOLDOWN_DURATION_MS) {
                return new ProbeResult(ProbeStatus.EXPIRED, json.optDouble("speedRatio", 0.0), ts);
            }
            ProbeStatus status = ProbeStatus.valueOf(json.optString("status", ProbeStatus.UNKNOWN.name()));
            return new ProbeResult(status, json.optDouble("speedRatio", 0.0), ts);
        } catch (Exception e) {
            return new ProbeResult(ProbeStatus.UNKNOWN, 0.0, 0L);
        }
    }

    public void recordFallbackEvent() {
        long now = System.currentTimeMillis();
        int count = prefs.getInt(KEY_FALLBACK_COUNT, 0);
        prefs.edit()
                .putInt(KEY_FALLBACK_COUNT, count + 1)
                .putLong(KEY_LAST_FALLBACK_TS, now)
                .apply();
    }

    public boolean isInFallbackCooldown() {
        long lastTs = prefs.getLong(KEY_LAST_FALLBACK_TS, 0L);
        int count = prefs.getInt(KEY_FALLBACK_COUNT, 0);
        if (count >= MAX_FALLBACKS_PER_WINDOW) {
            return (System.currentTimeMillis() - lastTs) < COOLDOWN_DURATION_MS;
        }
        return false;
    }

    public String getMaxAv1Rung() {
        return prefs.getString(KEY_MAX_RUNG, "540p");
    }

    public void setMaxAv1Rung(String rung) {
        prefs.edit().putString(KEY_MAX_RUNG, rung).apply();
    }
}
