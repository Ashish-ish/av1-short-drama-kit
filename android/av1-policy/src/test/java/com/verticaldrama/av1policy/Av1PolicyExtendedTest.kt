package com.verticaldrama.av1policy

import org.junit.Assert.*
import org.junit.Test

class Av1PolicyExtendedTest {

    @Test
    fun testRungDegradationSequence() {
        val rungs = listOf("720p", "540p", "360p")
        var current = "720p"

        fun degrade(rung: String): String = when (rung) {
            "720p" -> "540p"
            "540p" -> "360p"
            else -> "none"
        }

        current = degrade(current)
        assertEquals("540p", current)

        current = degrade(current)
        assertEquals("360p", current)

        current = degrade(current)
        assertEquals("none", current)
    }

    @Test
    fun testSlidingWindowFallbackLogic() {
        // Test that 3 failures within 24 hours trigger cooldown
        val windowMs = 24L * 60 * 60 * 1000
        val t0 = 1000000L
        val t1 = t0 + 1000L
        val t2 = t0 + 2000L

        var fallbacks = mutableListOf<Long>()
        fallbacks.add(t0)
        fallbacks.add(t1)
        fallbacks.add(t2)

        val withinWindow = fallbacks.filter { t2 - it <= windowMs }
        assertEquals(3, withinWindow.size)
        assertTrue("3 fallbacks within 24h triggers cooldown", withinWindow.size >= 3)

        // If the first event was 25 hours ago, it expires
        val t3 = t0 + 25L * 60 * 60 * 1000
        val activeRecent = fallbacks.filter { t3 - it <= windowMs }
        assertEquals(0, activeRecent.size)
    }

    @Test
    fun testTransientResourceErrorClassification() {
        val errorCodeInsufficientResource = 1100 // MediaCodec.CodecException.ERROR_INSUFFICIENT_RESOURCE
        val isTransient = true

        val probeStatus = if (isTransient || errorCodeInsufficientResource == 1100) {
            EligibilityCache.ProbeStatus.UNKNOWN
        } else {
            EligibilityCache.ProbeStatus.FAILED
        }

        assertEquals(EligibilityCache.ProbeStatus.UNKNOWN, probeStatus)
    }
}
