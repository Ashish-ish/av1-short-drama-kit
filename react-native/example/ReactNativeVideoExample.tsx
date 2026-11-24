import React, { useEffect, useState, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Video, { VideoRef } from 'react-native-video';
import { getReactNativeVideoConfig, MasterPlaylistSet, PlaybackProfile, DRAMA_BUFFER_CONFIG } from '../src';

const SAMPLE_MASTERS: MasterPlaylistSet = {
  h264: 'https://cdn.example.com/drama/ep01/master_h264.m3u8',
  hevc: 'https://cdn.example.com/drama/ep01/master_hevc.m3u8',
  av1: 'https://cdn.example.com/drama/ep01/master_av1.m3u8',
};

export function ReactNativeVideoDramaPlayer() {
  const [profile, setProfile] = useState<PlaybackProfile | null>(null);
  const [currentUrl, setCurrentUrl] = useState<string>('');
  const [isFallback, setIsFallback] = useState(false);
  const [playbackTime, setPlaybackTime] = useState<number>(0);
  const videoRef = useRef<VideoRef>(null);

  useEffect(() => {
    async function init() {
      const config = await getReactNativeVideoConfig(SAMPLE_MASTERS);
      setProfile(config.profile);
      setCurrentUrl(config.source.uri);
    }
    init();
  }, []);

  const handlePlaybackError = (error: any) => {
    console.warn('[DramaPlayer] Encountered error, executing mid-stream fallback to H.264', error);
    triggerFallback('RUNTIME_PLAYBACK_ERROR');
  };

  const triggerFallback = (reason: string) => {
    if (isFallback) return;
    setIsFallback(true);
    setCurrentUrl(SAMPLE_MASTERS.h264);
    videoRef.current?.seek(playbackTime);
  };

  return (
    <View style={styles.container}>
      {currentUrl ? (
        <Video
          ref={videoRef}
          source={{ uri: currentUrl, type: 'm3u8' }}
          style={styles.video}
          resizeMode="cover"
          repeat
          bufferConfig={DRAMA_BUFFER_CONFIG.reactNativeVideo}
          onProgress={(data) => setPlaybackTime(data.currentTime)}
          onError={handlePlaybackError}
        />
      ) : null}

      <View style={styles.hud}>
        <Text style={[styles.codecBadge, isFallback && styles.fallbackBadge]}>
          Active Codec: {isFallback ? 'H.264 (FALLBACK ACTIVE)' : profile?.codec.toUpperCase()} ({profile?.maxRung})
        </Text>
        <Text style={styles.reasonText}>Policy: {profile?.reasonCode}</Text>
        <Text style={styles.bufferText}>Buffer for Playback: 800ms (Fast TTFF)</Text>

        {!isFallback && (
          <TouchableOpacity style={styles.fallbackButton} onPress={() => triggerFallback('USER_DEBUG_TRIGGER')}>
            <Text style={styles.buttonText}>⚡ Test Mid-Stream Fallback</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  video: { width: '100%', height: '100%' },
  hud: {
    position: 'absolute',
    top: 50,
    left: 16,
    right: 16,
    backgroundColor: 'rgba(15, 23, 42, 0.85)',
    borderRadius: 8,
    padding: 12,
  },
  codecBadge: { color: '#10b981', fontWeight: 'bold', fontSize: 14 },
  fallbackBadge: { color: '#ef4444' },
  reasonText: { color: '#94a3b8', fontSize: 11, marginTop: 4 },
  bufferText: { color: '#cbd5e1', fontSize: 11, marginTop: 2 },
  fallbackButton: {
    marginTop: 8,
    backgroundColor: '#dc2626',
    borderRadius: 4,
    paddingVertical: 6,
    alignItems: 'center',
  },
  buttonText: { color: '#fff', fontSize: 11, fontWeight: '600' },
});
