import { MasterPlaylistSet, PlaybackProfile } from './policyBridge';

export interface ExpoVideoConfig {
  source: {
    uri: string;
  };
  preferredForwardBufferDuration: number;
  profile: PlaybackProfile;
}

export declare function getExpoVideoConfig(
  masters: MasterPlaylistSet,
  options?: { hasDrm?: boolean; forceH264?: boolean }
): Promise<ExpoVideoConfig>;\n