# AV1 Vertical Drama Bridge (React Native & Expo)

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
