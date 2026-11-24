import os
import shutil
import subprocess
import hashlib

REPO_ROOT = "/Users/ashish/Projects/av1decoder"
RN_DIR = os.path.join(REPO_ROOT, "react-native")
DIST_DIR = os.path.join(REPO_ROOT, "dist/expo")
BUILD_DIST = os.path.join(RN_DIR, "dist")

os.makedirs(DIST_DIR, exist_ok=True)
os.makedirs(BUILD_DIST, exist_ok=True)

# 1. Generate JS and .d.ts files

# policyBridge.js
policy_bridge_js = """
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
};
"""

policy_bridge_dts = """
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
): Promise<PlaybackProfile>;
"""

# expoVideoAdapter.js
expo_adapter_js = """
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
};
"""

expo_adapter_dts = """
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
): Promise<ExpoVideoConfig>;
"""

# reactNativeVideoAdapter.js
rn_adapter_js = """
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
};
"""

rn_adapter_dts = """
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
): Promise<ReactNativeVideoConfig>;
"""

# index.js
index_js = """
const policyBridge = require('./policyBridge');
const expoVideoAdapter = require('./expoVideoAdapter');
const reactNativeVideoAdapter = require('./reactNativeVideoAdapter');

module.exports = {
  ...policyBridge,
  ...expoVideoAdapter,
  ...reactNativeVideoAdapter,
};
"""

index_dts = """
export * from './policyBridge';
export * from './expoVideoAdapter';
export * from './reactNativeVideoAdapter';
"""

files = {
    "policyBridge.js": policy_bridge_js,
    "policyBridge.d.ts": policy_bridge_dts,
    "expoVideoAdapter.js": expo_adapter_js,
    "expoVideoAdapter.d.ts": expo_adapter_dts,
    "reactNativeVideoAdapter.js": rn_adapter_js,
    "reactNativeVideoAdapter.d.ts": rn_adapter_dts,
    "index.js": index_js,
    "index.d.ts": index_dts,
}

for filename, content in files.items():
    with open(os.path.join(BUILD_DIST, filename), "w") as f:
        f.write(content.strip() + "\\n")

# README.md for npm package
readme_content = """# AV1 Vertical Drama Bridge (React Native & Expo)

Cross-platform playback policy resolver, drama-tuned buffer configurations, and Expo Config Plugin.

## Installation

```bash
# In Expo projects
npx expo install av1-vertical-drama-bridge

# In React Native bare projects
npm install av1-vertical-drama-bridge
```

## Expo Video Usage

```typescript
import { useVideoPlayer, VideoView } from 'expo-video';
import { getExpoVideoConfig } from 'av1-vertical-drama-bridge';

const config = await getExpoVideoConfig({
  h264: 'https://cdn.example.com/master_h264.m3u8',
  hevc: 'https://cdn.example.com/master_hevc.m3u8',
  av1: 'https://cdn.example.com/master_av1.m3u8',
});

const player = useVideoPlayer(config.source.uri, player => {
  player.loop = true;
  player.play();
});
```

## License
Apache-2.0
"""
with open(os.path.join(RN_DIR, "README.md"), "w") as f:
    f.write(readme_content)

print(f"SUCCESS: Generated dist files in {BUILD_DIST}")

# 2. Run npm pack
cmd_pack = ["npm", "pack"]
result = subprocess.run(cmd_pack, cwd=RN_DIR, capture_output=True, text=True, check=True)
tgz_name = result.stdout.strip().splitlines()[-1]
src_tgz = os.path.join(RN_DIR, tgz_name)
dest_tgz = os.path.join(DIST_DIR, "av1-vertical-drama-bridge-0.1.0.tgz")

shutil.move(src_tgz, dest_tgz)
print(f"SUCCESS: Created NPM package tarball at {dest_tgz}")

# Checksum
with open(dest_tgz, "rb") as f:
    sha = hashlib.sha256(f.read()).hexdigest()

with open(os.path.join(DIST_DIR, "av1-vertical-drama-bridge-0.1.0.tgz.sha256"), "w") as f:
    f.write(f"{sha}  av1-vertical-drama-bridge-0.1.0.tgz\\n")

print(f"Expo / NPM package SHA-256: {sha}")
