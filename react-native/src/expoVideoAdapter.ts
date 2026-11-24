import { getPlaybackProfile, MasterPlaylistSet, PlaybackProfile, DRAMA_BUFFER_CONFIG } from './policyBridge';

export interface ExpoVideoConfig {
  source: {
    uri: string;
  };
  preferredForwardBufferDuration: number;
  profile: PlaybackProfile;
}

/**
 * Generates configuration for Expo Video (expo-video) useVideoPlayer.
 */
export async function getExpoVideoConfig(
  masters: MasterPlaylistSet,
  options?: { hasDrm?: boolean; forceH264?: boolean }
): Promise<ExpoVideoConfig> {
  const profile = await getPlaybackProfile(masters, options);

  return {
    source: {
      uri: profile.masterUrl,
    },
    preferredForwardBufferDuration: DRAMA_BUFFER_CONFIG.expoVideo.preferredForwardBufferDuration,
    profile,
  };
}
