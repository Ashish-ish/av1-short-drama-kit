const DRAMA_BUFFER_CONFIG = {
  reactNativeVideo: {
    minBufferMs: 5000,
    maxBufferMs: 15000,
    bufferForPlaybackMs: 800,
    bufferForPlaybackAfterRebufferMs: 2000,
  },
  expoVideo: {
    preferredForwardBufferDuration: 4.0,
  },
};

async function getPlaybackProfile(masters, options) {
  const hasDrm = options?.hasDrm ?? false;

  if (options?.forceH264) {
    return {
      masterUrl: masters.h264,
      codec: 'h264',
      maxRung: '720p',
      reasonCode: 'USER_OVERRIDE_H264',
      isHardwareDecode: true,
    };
  }

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

  const globalObj = globalThis;
  const NativeModules = globalObj?.ReactNative?.NativeModules || globalObj?.NativeModules;
  const bridge = NativeModules?.AV1PolicyModule;

  if (bridge && typeof bridge.getPlaybackProfile === 'function') {
    try {
      return await bridge.getPlaybackProfile(masters);
    } catch (e) {
      console.warn('[AV1PolicyBridge] Native module call failed, falling back to JS heuristic:', e);
    }
  }

  const platformOS = globalObj?.Platform?.OS || (typeof navigator !== 'undefined' && /iPhone|iPad/i.test(navigator.userAgent) ? 'ios' : 'android');

  if (platformOS === 'ios') {
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

  if (masters.av1) {
    return {
      masterUrl: masters.av1,
      codec: 'av1',
      maxRung: '540p',
      reasonCode: 'ANDROID_DAV1D_ELIGIBLE_JS_FALLBACK',
      isHardwareDecode: false,
    };
  }

  if (masters.hevc) {
    return {
      masterUrl: masters.hevc,
      codec: 'hevc',
      maxRung: '720p',
      reasonCode: 'PREFER_HARDWARE_HEVC_DEFAULT',
      isHardwareDecode: true,
    };
  }

  return {
    masterUrl: masters.h264,
    codec: 'h264',
    maxRung: '720p',
    reasonCode: 'DEFAULT_H264_BASELINE',
    isHardwareDecode: true,
  };
}

module.exports = {
  DRAMA_BUFFER_CONFIG,
  getPlaybackProfile,
};\n