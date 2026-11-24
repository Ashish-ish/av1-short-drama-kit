const test = require('node:test');
const assert = require('node:assert');

// Test the core decision logic
function evaluateProfile(masters, options, platform = 'android', apiLevel = 34) {
  if (options?.forceH264) {
    return { codec: 'h264', masterUrl: masters.h264, reason: 'USER_OVERRIDE_H264' };
  }
  if (options?.hasDrm) {
    if (masters.hevc) {
      return { codec: 'hevc', masterUrl: masters.hevc, reason: 'DRM_HARDWARE_HEVC_PREFERRED' };
    }
    return { codec: 'h264', masterUrl: masters.h264, reason: 'DRM_H264_REQUIRED' };
  }
  if (platform === 'ios') {
    if (masters.hevc) {
      return { codec: 'hevc', masterUrl: masters.hevc, reason: 'IOS_HARDWARE_HEVC_FALLBACK' };
    }
    return { codec: 'h264', masterUrl: masters.h264, reason: 'IOS_DEFAULT_H264' };
  }
  if (platform === 'android' && apiLevel >= 31 && masters.av1) {
    return { codec: 'av1', masterUrl: masters.av1, reason: 'ANDROID_DAV1D_ELIGIBLE_JS_FALLBACK' };
  }
  if (masters.hevc) {
    return { codec: 'hevc', masterUrl: masters.hevc, reason: 'PREFER_HARDWARE_HEVC_DEFAULT' };
  }
  return { codec: 'h264', masterUrl: masters.h264, reason: 'DEFAULT_H264_BASELINE' };
}

test('DRM content redirects away from software AV1', () => {
  const masters = {
    h264: 'https://cdn.example.com/master_h264.m3u8',
    hevc: 'https://cdn.example.com/master_hevc.m3u8',
    av1: 'https://cdn.example.com/master_av1.m3u8',
  };
  const profile = evaluateProfile(masters, { hasDrm: true });
  assert.strictEqual(profile.codec, 'hevc');
  assert.strictEqual(profile.reason, 'DRM_HARDWARE_HEVC_PREFERRED');
});

test('iOS defaults to hardware HEVC when AV1 hardware decode is absent', () => {
  const masters = {
    h264: 'https://cdn.example.com/master_h264.m3u8',
    hevc: 'https://cdn.example.com/master_hevc.m3u8',
    av1: 'https://cdn.example.com/master_av1.m3u8',
  };
  const profile = evaluateProfile(masters, {}, 'ios');
  assert.strictEqual(profile.codec, 'hevc');
  assert.strictEqual(profile.reason, 'IOS_HARDWARE_HEVC_FALLBACK');
});

test('Android 12+ (API 31+) selects AV1 master when eligible', () => {
  const masters = {
    h264: 'https://cdn.example.com/master_h264.m3u8',
    hevc: 'https://cdn.example.com/master_hevc.m3u8',
    av1: 'https://cdn.example.com/master_av1.m3u8',
  };
  const profile = evaluateProfile(masters, {}, 'android', 34);
  assert.strictEqual(profile.codec, 'av1');
  assert.strictEqual(profile.masterUrl, masters.av1);
});

test('Older Android (API < 31) falls back to HEVC/H.264', () => {
  const masters = {
    h264: 'https://cdn.example.com/master_h264.m3u8',
    hevc: 'https://cdn.example.com/master_hevc.m3u8',
    av1: 'https://cdn.example.com/master_av1.m3u8',
  };
  const profile = evaluateProfile(masters, {}, 'android', 29);
  assert.strictEqual(profile.codec, 'hevc');
});
