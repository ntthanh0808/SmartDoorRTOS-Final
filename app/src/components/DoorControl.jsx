import { useState } from 'react';
import { View, Text, TouchableOpacity, Alert, StyleSheet, ActivityIndicator } from 'react-native';
import api from '../api/axios';
import bleService from '../services/bleService';
import { useAuth } from '../context/AuthContext';

export default function DoorControl({ doorStatus, isLocked }) {
  const [loading, setLoading] = useState(false);
  const [bleScanning, setBleScanning] = useState(false);
  const { user } = useAuth();

  const handleAction = async (action) => {
    setLoading(true);
    try {
      await api.post(`/door/${action}`);
    } catch (err) {
      Alert.alert('Lỗi', err.response?.data?.detail || 'Lỗi');
    } finally {
      setLoading(false);
    }
  };

  const handleBLEOpen = async () => {
    setBleScanning(true);
    try {
      // Quét BLE beacon (10 giây thay vì 5 giây)
      const beaconData = await bleService.scanForBeacon(10000);
      
      // Gửi request mở cửa với beacon ID
      await api.post('/door/open-ble', {
        beacon_id: beaconData.beaconId
      });
      
      Alert.alert('✓ Thành công', 'Đã mở cửa!');
      
      // Ngắt kết nối BLE
      await bleService.disconnect();
      
    } catch (err) {
      Alert.alert(
        'Lỗi', 
        err.response?.data?.detail || err.message || 'Không thể mở cửa'
      );
    } finally {
      setBleScanning(false);
    }
  };

  const openDisabled =
    loading || bleScanning || isLocked || doorStatus === 'opened' || doorStatus === 'opening';
  const closeDisabled =
    loading || doorStatus === 'closed' || doorStatus === 'closing';

  // Admin dùng nút mở trực tiếp, user dùng BLE
  const isAdmin = user?.role === 'admin';

  return (
    <View style={styles.container}>
      {/* Nút mở cửa */}
      {isAdmin ? (
        <TouchableOpacity
          style={[styles.btn, styles.openBtn, openDisabled && styles.disabled]}
          onPress={() => handleAction('open')}
          disabled={openDisabled}
        >
          <Text style={styles.btnText}>Mở cửa</Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity
          style={[styles.btn, styles.bleBtn, openDisabled && styles.disabled]}
          onPress={handleBLEOpen}
          disabled={openDisabled}
        >
          {bleScanning ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator color="#fff" />
              <Text style={styles.loadingText}>Đang quét...</Text>
            </View>
          ) : (
            <>
              <Text style={styles.btnText}>Mở cửa</Text>
              <Text style={styles.subText}>Cần ở gần cửa</Text>
            </>
          )}
        </TouchableOpacity>
      )}

      {/* Nút đóng cửa */}
      <TouchableOpacity
        style={[styles.btn, styles.closeBtn, closeDisabled && styles.disabled]}
        onPress={() => handleAction('close')}
        disabled={closeDisabled}
      >
        <Text style={styles.btnText}>Đóng cửa</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 12 },
  btn: { paddingVertical: 16, borderRadius: 8, alignItems: 'center' },
  openBtn: { backgroundColor: '#16a34a' },
  bleBtn: { backgroundColor: '#2563eb' },
  closeBtn: { backgroundColor: '#dc2626' },
  disabled: { opacity: 0.4 },
  btnText: { color: '#fff', fontWeight: '600', fontSize: 16 },
  subText: { color: '#ddd', fontSize: 12, marginTop: 4 },
  loadingContainer: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  loadingText: { color: '#fff', fontSize: 14 },
});
