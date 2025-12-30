import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, Image, ActivityIndicator, Alert } from 'react-native';
import * as FileSystem from 'expo-file-system';
import * as MediaLibrary from 'expo-media-library';
import { Video } from 'expo-av';

// Replace with your local IP address when running on device
const API_URL = 'http://192.168.1.100:8000'; 

export default function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [media, setMedia] = useState([]);

  const analyzeUrl = async () => {
    if (!url) return;
    setLoading(true);
    setMedia([]);

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed to analyze');
      
      setMedia(data.media || []);
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadMedia = async (mediaUrl, type) => {
    try {
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Please grant permission to save to gallery');
        return;
      }

      const filename = mediaUrl.split('/').pop().split('?')[0] || `download.${type === 'image' ? 'jpg' : 'mp4'}`;
      const fileUri = FileSystem.documentDirectory + filename;

      // Use proxy download if needed, or direct if headers allow
      // For this demo, we try direct first, but in production, use the proxy endpoint
      const downloadRes = await FileSystem.downloadAsync(
        `${API_URL}/api/proxy_download?url=${encodeURIComponent(mediaUrl)}`,
        fileUri
      );

      if (downloadRes.status === 200) {
        const asset = await MediaLibrary.createAssetAsync(downloadRes.uri);
        await MediaLibrary.createAlbumAsync('SocialDownloader', asset, false);
        Alert.alert('Success', 'Saved to Gallery!');
      } else {
        throw new Error('Download failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to download: ' + error.message);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Social Downloader</Text>
      </View>

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder="Paste Link (IG, FB, Threads)"
          value={url}
          onChangeText={setUrl}
          autoCapitalize="none"
        />
        <TouchableOpacity style={styles.button} onPress={analyzeUrl} disabled={loading}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Analyze</Text>}
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.results}>
        {media.map((item, index) => (
          <View key={index} style={styles.card}>
            {item.type === 'image' ? (
              <Image source={{ uri: item.url }} style={styles.preview} />
            ) : (
              <Video
                source={{ uri: item.url }}
                style={styles.preview}
                useNativeControls
                resizeMode="contain"
              />
            )}
            <TouchableOpacity 
              style={styles.downloadBtn}
              onPress={() => downloadMedia(item.url, item.type)}
            >
              <Text style={styles.downloadText}>Download {item.quality || ''}</Text>
            </TouchableOpacity>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    paddingTop: 50,
  },
  header: {
    padding: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  inputContainer: {
    padding: 20,
    backgroundColor: '#fff',
    margin: 16,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#4f46e5',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  results: {
    flex: 1,
    padding: 16,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  preview: {
    width: '100%',
    height: 200,
    borderRadius: 8,
    backgroundColor: '#eee',
  },
  downloadBtn: {
    marginTop: 12,
    backgroundColor: '#10b981',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  downloadText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});
