import { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, RefreshControl, Switch, TextInput, Platform } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import api from '../api/axios';

export default function ScheduleScreen() {
  const [schedules, setSchedules] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  
  // Auto schedule config
  const [autoEnabled, setAutoEnabled] = useState(false);
  const [startTime, setStartTime] = useState(new Date());
  const [endTime, setEndTime] = useState(new Date());
  const [showStartPicker, setShowStartPicker] = useState(false);
  const [showEndPicker, setShowEndPicker] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const fetchSchedules = async () => {
    try {
      const { data } = await api.get('/schedules');
      setSchedules(data);
    } catch (error) {
      console.error('Error fetching schedules:', error);
    }
  };

  const loadAutoSchedule = async () => {
    try {
      const { data } = await api.get('/door/schedule');
      setAutoEnabled(data.enabled || false);
      
      if (data.start_time) {
        const [hours, minutes] = data.start_time.split(':');
        const date = new Date();
        date.setHours(parseInt(hours), parseInt(minutes), 0);
        setStartTime(date);
      }
      
      if (data.end_time) {
        const [hours, minutes] = data.end_time.split(':');
        const date = new Date();
        date.setHours(parseInt(hours), parseInt(minutes), 0);
        setEndTime(date);
      }
    } catch (error) {
      console.error('Error loading auto schedule:', error);
    }
  };

  useEffect(() => {
    fetchSchedules();
    loadAutoSchedule();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchSchedules();
    await loadAutoSchedule();
    setRefreshing(false);
  };

  const saveAutoSchedule = async () => {
    setSaving(true);
    setMessage('');
    
    try {
      const formatTime = (date) => {
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${hours}:${minutes}`;
      };

      await api.post('/door/schedule', {
        enabled: autoEnabled,
        start_time: autoEnabled ? formatTime(startTime) : null,
        end_time: autoEnabled ? formatTime(endTime) : null,
      });
      
      setMessage('✓ Đã lưu cấu hình');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage('✗ ' + (err.response?.data?.detail || 'Lỗi khi lưu'));
    } finally {
      setSaving(false);
    }
  };

  const toggleSchedule = async (id, currentStatus) => {
    try {
      await api.patch(`/schedules/${id}`, { is_active: !currentStatus });
      fetchSchedules();
    } catch (err) {
      Alert.alert('Lỗi', err.response?.data?.detail || 'Không thể cập nhật');
    }
  };

  const deleteSchedule = (id) => {
    Alert.alert(
      'Xác nhận',
      'Xóa lịch này?',
      [
        { text: 'Hủy', style: 'cancel' },
        {
          text: 'Xóa',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/schedules/${id}`);
              fetchSchedules();
            } catch (err) {
              Alert.alert('Lỗi', err.response?.data?.detail || 'Không thể xóa');
            }
          },
        },
      ]
    );
  };

  const addSchedule = () => {
    Alert.alert('Thông báo', 'Chức năng thêm lịch đang phát triển');
  };

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#2563eb']} />
        }
      >
        {/* Auto Schedule Config */}
        <View style={styles.configCard}>
          <View style={styles.configHeader}>
            <Switch
              value={autoEnabled}
              onValueChange={setAutoEnabled}
              trackColor={{ false: '#d1d5db', true: '#93c5fd' }}
              thumbColor={autoEnabled ? '#2563eb' : '#f3f4f6'}
            />
            <Text style={styles.configTitle}>Tự động đóng/mở hệ thống</Text>
          </View>

          {autoEnabled && (
            <View style={styles.timeInputs}>
              <View style={styles.timeInput}>
                <Text style={styles.timeLabel}>Giờ bắt đầu</Text>
                <TouchableOpacity
                  style={styles.timeButton}
                  onPress={() => setShowStartPicker(true)}
                >
                  <Text style={styles.timeText}>
                    {startTime.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', hour12: false })}
                  </Text>
                </TouchableOpacity>
              </View>

              <View style={styles.timeInput}>
                <Text style={styles.timeLabel}>Giờ kết thúc</Text>
                <TouchableOpacity
                  style={styles.timeButton}
                  onPress={() => setShowEndPicker(true)}
                >
                  <Text style={styles.timeText}>
                    {endTime.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', hour12: false })}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          <TouchableOpacity
            style={[styles.saveButton, saving && styles.saveButtonDisabled]}
            onPress={saveAutoSchedule}
            disabled={saving}
          >
            <Text style={styles.saveButtonText}>
              {saving ? 'Đang lưu...' : 'Lưu cấu hình'}
            </Text>
          </TouchableOpacity>

          {message ? (
            <Text style={[styles.message, message.startsWith('✓') ? styles.messageSuccess : styles.messageError]}>
              {message}
            </Text>
          ) : null}
        </View>

        {/* Time Pickers */}
        {showStartPicker && (
          <DateTimePicker
            value={startTime}
            mode="time"
            is24Hour={true}
            display="default"
            onChange={(event, selectedDate) => {
              setShowStartPicker(false);
              if (selectedDate) setStartTime(selectedDate);
            }}
          />
        )}

        {showEndPicker && (
          <DateTimePicker
            value={endTime}
            mode="time"
            is24Hour={true}
            display="default"
            onChange={(event, selectedDate) => {
              setShowEndPicker(false);
              if (selectedDate) setEndTime(selectedDate);
            }}
          />
        )}

        {/* Schedule List Title */}
        <Text style={styles.sectionTitle}>Lịch đã tạo</Text>
        {schedules.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>Chưa có lịch tự động</Text>
            <Text style={styles.emptySubtext}>Nhấn + để thêm lịch mới</Text>
          </View>
        ) : (
          schedules.map((schedule) => (
            <View key={schedule.id} style={styles.card}>
              <View style={styles.cardHeader}>
                <View style={styles.cardTitle}>
                  <Text style={styles.time}>{schedule.time}</Text>
                  <Text style={styles.action}>
                    {schedule.action === 'lock' ? '🔒 Khóa hệ thống' : '🔓 Mở khóa hệ thống'}
                  </Text>
                </View>
                <Switch
                  value={schedule.is_active}
                  onValueChange={() => toggleSchedule(schedule.id, schedule.is_active)}
                  trackColor={{ false: '#d1d5db', true: '#93c5fd' }}
                  thumbColor={schedule.is_active ? '#2563eb' : '#f3f4f6'}
                />
              </View>
              
              {schedule.days && schedule.days.length > 0 && (
                <View style={styles.daysContainer}>
                  {schedule.days.map((day, idx) => (
                    <View key={idx} style={styles.dayBadge}>
                      <Text style={styles.dayText}>{day}</Text>
                    </View>
                  ))}
                </View>
              )}

              <TouchableOpacity
                style={styles.deleteBtn}
                onPress={() => deleteSchedule(schedule.id)}
              >
                <Text style={styles.deleteBtnText}>Xóa</Text>
              </TouchableOpacity>
            </View>
          ))
        )}
      </ScrollView>

      <TouchableOpacity style={styles.fab} onPress={addSchedule}>
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f3f4f6' },
  content: { padding: 16, gap: 12, paddingBottom: 80 },
  
  // Auto config card
  configCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 3,
    elevation: 2,
    gap: 16,
  },
  configHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  configTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    flex: 1,
  },
  timeInputs: {
    flexDirection: 'row',
    gap: 12,
    paddingLeft: 8,
  },
  timeInput: {
    flex: 1,
  },
  timeLabel: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 6,
  },
  timeButton: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 12,
    backgroundColor: '#fff',
  },
  timeText: {
    fontSize: 16,
    color: '#1f2937',
    fontFamily: 'monospace',
    textAlign: 'center',
  },
  saveButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  saveButtonDisabled: {
    opacity: 0.5,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
  message: {
    fontSize: 13,
    textAlign: 'center',
  },
  messageSuccess: {
    color: '#16a34a',
  },
  messageError: {
    color: '#dc2626',
  },
  
  // Section title
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#374151',
    marginTop: 8,
  },
  
  // Schedule cards
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 3,
    elevation: 2,
    gap: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTitle: { flex: 1 },
  time: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1f2937',
    fontFamily: 'monospace',
  },
  action: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
  },
  daysContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  dayBadge: {
    backgroundColor: '#eff6ff',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  dayText: {
    fontSize: 12,
    color: '#2563eb',
    fontWeight: '500',
  },
  deleteBtn: {
    alignSelf: 'flex-start',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    backgroundColor: '#fee2e2',
  },
  deleteBtnText: {
    color: '#dc2626',
    fontSize: 13,
    fontWeight: '500',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 16,
    color: '#6b7280',
    fontWeight: '500',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 8,
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#2563eb',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  fabText: {
    fontSize: 32,
    color: '#fff',
    fontWeight: '300',
  },
});
