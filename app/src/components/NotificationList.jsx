import { View, Text, FlatList, StyleSheet } from 'react-native';

const CATEGORY_COLOR = {
  access: '#22c55e',    // Xanh lá - Truy cập thành công
  alert: '#ef4444',     // Đỏ - Cảnh báo
  motion: '#eab308',    // Vàng - Chuyển động
  lock: '#ef4444',      // Đỏ - Khóa hệ thống
  unlock: '#22c55e',    // Xanh lá - Mở khóa hệ thống
  schedule: '#3b82f6',  // Xanh dương - Lịch tự động
  system: '#6b7280',    // Xám - Hệ thống
};

const CATEGORY_BG = {
  access: '#f0fdf4',    // Nền xanh nhạt
  alert: '#fef2f2',     // Nền đỏ nhạt
  motion: '#fefce8',    // Nền vàng nhạt
  lock: '#fef2f2',      // Nền đỏ nhạt
  unlock: '#f0fdf4',    // Nền xanh nhạt
  schedule: '#eff6ff',  // Nền xanh dương nhạt
  system: '#f9fafb',    // Nền xám nhạt
};

const CATEGORY_TEXT = {
  access: '#166534',    // Chữ xanh đậm
  alert: '#991b1b',     // Chữ đỏ đậm
  motion: '#854d0e',    // Chữ vàng đậm
  lock: '#991b1b',      // Chữ đỏ đậm
  unlock: '#166534',    // Chữ xanh đậm
  schedule: '#1e40af',  // Chữ xanh dương đậm
  system: '#374151',    // Chữ xám đậm
};

export default function NotificationList({ notifications, connected = false }) {
  if (!connected) {
    return <Text style={styles.disconnected}>Chưa được kết nối</Text>;
  }

  if (!notifications.length) {
    return <Text style={styles.empty}>Chưa có thông báo</Text>;
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={notifications}
        keyExtractor={(item) => String(item.id)}
        style={styles.list}
        nestedScrollEnabled={true}
        showsVerticalScrollIndicator={true}
        renderItem={({ item }) => (
          <View
            style={[
              styles.item,
              { 
                borderLeftColor: CATEGORY_COLOR[item.category] ?? '#9ca3af',
                backgroundColor: CATEGORY_BG[item.category] ?? '#fff',
              },
            ]}
          >
            <Text style={[
              styles.message,
              { color: CATEGORY_TEXT[item.category] ?? '#1f2937' }
            ]}>
              {item.message}
            </Text>
            <Text style={styles.time}>
              {(item.time instanceof Date ? item.time : new Date(item.time))
                .toLocaleTimeString('vi-VN')}
            </Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  empty: { color: '#9ca3af', fontSize: 13 },
  disconnected: { color: '#ef4444', fontSize: 13, fontWeight: '500' },
  container: { 
    height: 320,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    overflow: 'hidden',
  },
  list: { 
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  item: {
    borderLeftWidth: 4,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 1,
  },
  message: { 
    fontSize: 13, 
    marginBottom: 4,
    fontWeight: '500',
  },
  time: { fontSize: 11, color: '#9ca3af' },
});
