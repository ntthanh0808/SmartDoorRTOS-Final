import { useState, useEffect } from 'react';
import FaceCaptureModal from './FaceCaptureModal';
import api from '../api/axios';

export default function UserForm({ user, onSubmit, onCancel }) {
  const isEdit = !!user;
  const [form, setForm] = useState({
    username: '',
    password: '',
    full_name: '',
    role: 'user',
    card_uid: '',
  });
  const [faceImages, setFaceImages] = useState([]);
  const [showFaceCapture, setShowFaceCapture] = useState(false);

  useEffect(() => {
    if (user) {
      setForm({
        username: user.username,
        password: '',
        full_name: user.full_name,
        role: user.role,
        card_uid: user.card_uid || '',
      });
    }
  }, [user]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleFaceCapture = (images) => {
    setFaceImages(images);
  };

  const handleReplaceFace = async () => {
    if (!confirm('Bạn có chắc muốn thay đổi khuôn mặt? Dữ liệu cũ sẽ bị xóa.')) {
      return;
    }

    try {
      // Delete old face data from dataset
      const folderName = user.full_name;
      await api.delete(`/face/delete-folder/${encodeURIComponent(folderName)}`);

      // Open camera to capture new face
      setShowFaceCapture(true);
    } catch (err) {
      console.error('Error deleting face data:', err);
      alert('Lỗi khi xóa dữ liệu cũ');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = { ...form };
    if (isEdit && !data.password) delete data.password;
    if (!data.card_uid) data.card_uid = null;
    
    // Pass face images along with form data
    onSubmit(data, faceImages);
  };

  const handleCancel = () => {
    // Reset face images when canceling
    setFaceImages([]);
    onCancel();
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow space-y-4">
        <h3 className="text-lg font-semibold">{isEdit ? 'Sửa người dùng' : 'Thêm người dùng'}</h3>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <input name="username" value={form.username} onChange={handleChange} disabled={isEdit}
              className="w-full border rounded px-3 py-2 text-sm disabled:bg-gray-100" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mật khẩu {isEdit && <span className="text-gray-400">(để trống nếu không đổi)</span>}
            </label>
            <input name="password" type="password" value={form.password} onChange={handleChange}
              className="w-full border rounded px-3 py-2 text-sm" {...(!isEdit && { required: true })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Họ tên</label>
            <input name="full_name" value={form.full_name} onChange={handleChange}
              className="w-full border rounded px-3 py-2 text-sm" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Vai trò</label>
            <select name="role" value={form.role} onChange={handleChange}
              className="w-full border rounded px-3 py-2 text-sm">
              <option value="user">Người dùng</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Mã thẻ RFID</label>
            <input name="card_uid" value={form.card_uid} onChange={handleChange}
              className="w-full border rounded px-3 py-2 text-sm font-mono" placeholder="VD: AB:CD:EF:12" />
          </div>
          
          {/* Face capture section */}
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {isEdit ? 'Thay đổi khuôn mặt' : 'Thêm khuôn mặt'}
            </label>
            <div className="flex items-center gap-3">
              {isEdit ? (
                <button
                  type="button"
                  onClick={handleReplaceFace}
                  className="px-4 py-2 bg-orange-600 text-white rounded text-sm hover:bg-orange-700 transition-colors"
                >
                  Thay đổi khuôn mặt
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setShowFaceCapture(true)}
                  className="px-4 py-2 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 transition-colors"
                >
                  Chụp khuôn mặt
                </button>
              )}
              {faceImages.length > 0 && (
                <span className="text-sm text-green-600 font-medium">
                  ✓ Đã chụp {faceImages.length} ảnh mới
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {isEdit 
                ? 'Thay đổi khuôn mặt sẽ xóa dữ liệu cũ và chụp lại'
                : 'Chụp khuôn mặt để sử dụng tính năng nhận diện khi mở cửa'
              }
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
            {isEdit ? 'Cập nhật' : 'Tạo'}
          </button>
          <button type="button" onClick={handleCancel} className="px-4 py-2 bg-gray-200 rounded text-sm hover:bg-gray-300">
            Hủy
          </button>
        </div>
      </form>

      <FaceCaptureModal
        isOpen={showFaceCapture}
        onClose={() => setShowFaceCapture(false)}
        onCapture={handleFaceCapture}
      />
    </>
  );
}
