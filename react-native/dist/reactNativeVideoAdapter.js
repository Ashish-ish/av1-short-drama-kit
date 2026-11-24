const { getPlaybackProfile, DRAMA_BUFFER_CONFIG } = require('./policyBridge');

async function getReactNativeVideoConfig(masters, options) {
  const profile = await getPlaybackProfile(masters, options);
  return {
    source: {
      uri: profile.masterUrl,
      type: 'm3u8',
    },
    bufferConfig: DRAMA_BUFFER_CONFIG.reactNativeVideo,
    profile,
  };
}

module.exports = {
  getReactNativeVideoConfig,
};\n