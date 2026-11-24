import { getPlaybackProfile, MasterPlaylistSet, PlaybackProfile, DRAMA_BUFFER_CONFIG } from './policyBridge';

export interface ReactNativeVideoConfig {
  source: {
    uri: string;
    type?: string;
  };
  bufferConfig: {
    minBufferMs: number;
    maxBufferMs: number;
    bufferForPlaybackMs: number;
    bufferForPlaybackAfterRebufferMs: number;
  };
  profile: PlaybackProfile;
}

/**
 * Generates props for react-native-video <Video /> component.
 */
export async function getReactNativeVideoConfig(
  masters: MasterPlaylistSet,
  options?: { hasDrm?: boolean; forceH264?: boolean }
): Promise<ReactNativeVideoConfig> {
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
