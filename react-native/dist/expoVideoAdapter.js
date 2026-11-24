const { getPlaybackProfile, DRAMA_BUFFER_CONFIG } = require('./policyBridge');

async function getExpoVideoConfig(masters, options) {
  const profile = await getPlaybackProfile(masters, options);
  return {
    source: {
      uri: profile.masterUrl,
    },
    preferredForwardBufferDuration: DRAMA_BUFFER_CONFIG.expoVideo.preferredForwardBufferDuration,
    profile,
  };
}

module.exports = {
  getExpoVideoConfig,
};\n