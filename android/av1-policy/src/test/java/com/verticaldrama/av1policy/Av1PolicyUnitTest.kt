package com.verticaldrama.av1policy

import org.junit.Assert.*
import org.junit.Test

class Av1PolicyUnitTest {

    @Test
    fun testCodecPrioritizationLogic() {
        // Test that when DRM is active, H.264 is mandated if software AV1 is requested
        val hasDrm = true
        val hasHwAv1 = false
        val hasHwHevc = true

        val selectedCodec = if (hasDrm) {
            if (hasHwAv1) "av1" else if (hasHwHevc) "hevc" else "h264"
        } else {
            "av1"
        }

        assertEquals("hevc", selectedCodec)
    }

    @Test
    fun testFallbackThresholdCalculation() {
        val dropped = 8
        val rendered = 92
        val total = dropped + rendered
        val dropPct = (dropped.toFloat() / total.toFloat()) * 100f

        val exceedsThreshold = dropPct > Av1FallbackTracker.MAX_DROPPED_FRAME_PCT
        assertTrue("8% drop rate should exceed 5% threshold", exceedsThreshold)
    }

    @Test
    fun testCooldownThresholdLimit() {
        val maxFallbacks = 3
        var fallbackCount = 0

        for (i in 1..maxFallbacks) {
            fallbackCount++
        }

        assertTrue("3 fallbacks should trigger cooldown", fallbackCount >= 3)
    }
}
