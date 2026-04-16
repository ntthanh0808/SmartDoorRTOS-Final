import { useState, useEffect } from 'react';
import api from '../api/axios';

export default function ScheduleConfig() {
  const [enabled, setEnabled] = useState(false);
  const [startTime, setStartTime] = useState('08:00');
  const [endTime, setEndTime] = useState('18:00');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadSchedule();
  }, []);

  const loadSchedule = async () => {
    try {
      const { data } = await api.get('/door/schedule');
      setEnabled(data.enabled || false);
      setStartTime(data.start_time || '08:00');
      setEndTime(data.end_time || '18:00');
    } catch (err) {
      console.error('Error loading schedule:', err);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      await api.post('/door/schedule', {
        enabled,
        start_time: enabled ? startTime : null,
        end_time: enabled ? endTime : null
      });
      setMessage('✓ Đã lưu cấu hình');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage('✗ ' + (err.response?.data?.detail || 'Lỗi khi lưu'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <div className="space-y-4">
        {/* Toggle */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="schedule-enabled"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
          />
          <label htmlFor="schedule-enabled" className="text-gray-700 font-medium cursor-pointer">
            Tự động đóng/mở hệ thống
          </label>
        </div>

        {/* Time inputs */}
        {enabled && (
          <div className="grid grid-cols-2 gap-4 pl-8">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Giờ bắt đầu</label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Giờ kết thúc</label>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {/* Save button */}
        <button
          onClick={handleSave}
          disabled={loading}
          className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Đang lưu...' : 'Lưu cấu hình'}
        </button>

        {/* Message */}
        {message && (
          <p className={`text-sm text-center ${message.startsWith('✓') ? 'text-green-600' : 'text-red-600'}`}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
}
