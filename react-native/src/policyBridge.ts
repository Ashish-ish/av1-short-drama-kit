export interface MasterPlaylistSet {
  h264: string;
  hevc?: string;
  av1?: string;
}

export type CodecType = 'av1' | 'hevc' | 'h264';
export type RungTier = '360p' | '540p' | '720p' | '1080p';

export interface PlaybackProfile {
  masterUrl: string;
  codec: CodecType;
  maxRung: RungTier;
  reasonCode: string;
  isHardwareDecode: boolean;
}

export interface DramaBufferConfig {
  reactNativeVideo: {
    minBufferMs: number;
    maxBufferMs: number;
    bufferForPlaybackMs: number;
    bufferForPlaybackAfterRebufferMs: number;
  };
  expoVideo: {
    preferredForwardBufferDuration: number;
  };
}

/**
 * Drama-tuned buffer settings.
 * Standard ExoPlayer/AVPlayer buffer defaults (2500-5000ms start threshold) are conservative.
 * Lowering bufferForPlaybackMs to 800ms dramatically improves startup (TTFF) without raising rebuffering
 * when paired with 2-second fMP4 CMAF segments.
 */
export const DRAMA_BUFFER_CONFIG: DramaBufferConfig = {
  reactNativeVideo: {
    minBufferMs: 5000,
    maxBufferMs: 15000,
    bufferForPlaybackMs: 800,
    bufferForPlaybackAfterRebufferMs: 2000,
  },
  expoVideo: {
    preferredForwardBufferDuration: 4.0, // 4 seconds forward buffer
  },
};

/**
 * Resolves the optimal playback profile without requiring app developers to fork players.
 */
export async function getPlaybackProfile(
  masters: MasterPlaylistSet,
  options?: {
    hasDrm?: boolean;
    forceH264?: boolean;
    isNativeModuleAvailable?: boolean;
  }
): Promise<PlaybackProfile> {
  const hasDrm = options?.hasDrm ?? false;

  // 1. Forced H.264 override
  if (options?.forceH264) {
    return {
      masterUrl: masters.h264,
      codec: 'h264',
      maxRung: '720p',
      reasonCode: 'USER_OVERRIDE_H264',
      isHardwareDecode: true,
    };
  }

  // 2. DRM content rule: Software decoders lack Widevine L1
  if (hasDrm) {
    if (masters.hevc) {
      return {
        masterUrl: masters.hevc,
        codec: 'hevc',
        maxRung: '720p',
        reasonCode: 'DRM_HARDWARE_HEVC_PREFERRED',
        isHardwareDecode: true,
      };
    }
    return {
      masterUrl: masters.h264,
      codec: 'h264',
      maxRung: '720p',
      reasonCode: 'DRM_H264_REQUIRED',
      isHardwareDecode: true,
    };
  }

  // 3. Check for native bridge module if available in React Native environment
  const globalObj = globalThis as any;
  const NativeModules = globalObj?.ReactNative?.NativeModules || globalObj?.NativeModules;
  const bridge = NativeModules?.AV1PolicyModule;

  if (bridge && typeof bridge.getPlaybackProfile === 'function') {
    try {
      const nativeProfile = await bridge.getPlaybackProfile(masters);
      return nativeProfile;
    } catch (e) {
      console.warn('[AV1PolicyBridge] Native module call failed, falling back to JS heuristics', e);
    }
  }

  // 4. Isomorphic JS Heuristic Fallback
  // On iOS without verified native hardware AV1 check, default safely to HEVC or H.264
  const platformOS = globalObj?.Platform?.OS || 'web';
  const osVersion = parseInt(String(globalObj?.Platform?.Version || '31'), 10);

  if (platformOS === 'ios') {
    // Hardware HEVC is ubiquitous on iOS; hardware AV1 requires iPhone 15 Pro / A17 Pro or M3+
    if (masters.hevc) {
      return {
        masterUrl: masters.hevc,
        codec: 'hevc',
        maxRung: '720p',
        reasonCode: 'IOS_HARDWARE_HEVC_FALLBACK',
        isHardwareDecode: true,
      };
    }
    return {
      masterUrl: masters.h264,
      codec: 'h264',
      maxRung: '720p',
      reasonCode: 'IOS_DEFAULT_H264',
      isHardwareDecode: true,
    };
  }

  // On Android: Android 12+ (API 31+) is eligible for platform dav1d
  if (platformOS === 'android' && osVersion >= 31 && masters.av1) {
    return {
      masterUrl: masters.av1,
      codec: 'av1',
      maxRung: '540p',
      reasonCode: 'ANDROID_DAV1D_ELIGIBLE_JS_FALLBACK',
      isHardwareDecode: false,
    };
  }

  // Prefer hardware HEVC if available
  if (masters.hevc) {
    return {
      masterUrl: masters.hevc,
      codec: 'hevc',
      maxRung: '720p',
      reasonCode: 'PREFER_HARDWARE_HEVC_DEFAULT',
      isHardwareDecode: true,
    };
  }

  // Default baseline H.264
  return {
    masterUrl: masters.h264,
    codec: 'h264',
    maxRung: '720p',
    reasonCode: 'DEFAULT_H264_BASELINE',
    isHardwareDecode: true,
  };
}
