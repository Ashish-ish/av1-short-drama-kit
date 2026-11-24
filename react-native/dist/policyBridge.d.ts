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

export declare const DRAMA_BUFFER_CONFIG: DramaBufferConfig;

export declare function getPlaybackProfile(
  masters: MasterPlaylistSet,
  options?: {
    hasDrm?: boolean;
    forceH264?: boolean;
    isNativeModuleAvailable?: boolean;
  }
): Promise<PlaybackProfile>;\n