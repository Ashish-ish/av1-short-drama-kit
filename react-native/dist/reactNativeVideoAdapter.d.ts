import { MasterPlaylistSet, PlaybackProfile } from './policyBridge';

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

export declare function getReactNativeVideoConfig(
  masters: MasterPlaylistSet,
  options?: { hasDrm?: boolean; forceH264?: boolean }
): Promise<ReactNativeVideoConfig>;\n