import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useVideoPlayer, VideoView } from 'expo-video';
import { getExpoVideoConfig, MasterPlaylistSet, PlaybackProfile } from '../src';

const SAMPLE_MASTERS: MasterPlaylistSet = {
  h264: 'https://cdn.example.com/drama/ep01/master_h264.m3u8',
  hevc: 'https://cdn.example.com/drama/ep01/master_hevc.m3u8',
  av1: 'https://cdn.example.com/drama/ep01/master_av1.m3u8',
};

export function ExpoVideoDramaPlayer() {
  const [profile, setProfile] = useState<PlaybackProfile | null>(null);
  const [isFallback, setIsFallback] = useState(false);

  useEffect(() => {
    async function init() {
      const config = await getExpoVideoConfig(SAMPLE_MASTERS);
      setProfile(config.profile);
    }
    init();
  }, []);

  const player = useVideoPlayer(profile?.masterUrl ?? '', (p) => {
    p.loop = true;
    p.play();
  });

  const handleForceFallback = () => {
    setIsFallback(true);
    if (profile && player) {
      const resumeSec = player.currentTime;
      player.replace(SAMPLE_MASTERS.h264);
      player.currentTime = resumeSec;
      player.play();
    }
  };

  if (!profile) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#10b981" />
        <Text style={styles.loadingText}>Evaluating Device AV1/HEVC Policy...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <VideoView style={styles.video} player={player} allowsFullscreen allowsPictureInPicture />

      {/* Drama HUD Overlay */}
      <View style={styles.hud}>
        <Text style={[styles.codecBadge, isFallback && styles.fallbackBadge]}>
          Active Codec: {isFallback ? 'H.264 (FALLBACK ACTIVE)' : profile.codec.toUpperCase()} ({profile.maxRung})
        </Text>
        <Text style={styles.reasonText}>Policy: {profile.reasonCode}</Text>
        <Text style={styles.bufferText}>Forward Buffer: 4.0s (Drama-Tuned)</Text>

        {!isFallback && (
          <TouchableOpacity style={styles.fallbackButton} onPress={handleForceFallback}>
            <Text style={styles.buttonText}>⚡ Test Fallback to H.264</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  center: { flex: 1, backgroundColor: '#000', justifyContent: 'center', alignItems: 'center' },
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
  loadingText: { color: '#94a3b8', marginTop: 12, fontSize: 13 },
  fallbackButton: {
    marginTop: 8,
    backgroundColor: '#dc2626',
    borderRadius: 4,
    paddingVertical: 6,
    alignItems: 'center',
  },
  buttonText: { color: '#fff', fontSize: 11, fontWeight: '600' },
});
