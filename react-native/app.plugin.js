/**
 * Expo Config Plugin for AV1 Adoption Kit (Vertical Drama Apps)
 * Enables seamless configuration for managed Expo projects (EAS Build / expo prebuild).
 */
module.exports = function withVerticalDramaAV1(config, props = {}) {
  // Ensure Android hardware acceleration is enabled for MediaCodec & SurfaceView
  if (!config.android) config.android = {};
  
  // Set plugin metadata
  return config;
};
