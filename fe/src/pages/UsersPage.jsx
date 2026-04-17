import { useState, useEffect } from 'react';
import api from '../api/axios';
import UserTable from '../components/UserTable';
import UserForm from '../components/UserForm';

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [editUser, setEditUser] = useState(null);
  const [showForm, setShowForm] = useState(false);

  const fetchUsers = () => api.get('/users').then(({ data }) => setUsers(data));

  useEffect(() => { fetchUsers(); }, []);

  const handleCreate = async (data, faceImages) => {
    try {
      // Create user first
      const response = await api.post('/users', data);
      const userId = response.data.id;

      // Upload face images if provided
      if (faceImages && faceImages.length > 0) {
        const formData = new FormData();
        faceImages.forEach((blob, index) => {
          formData.append('images', blob, `face_${index}.jpg`);
        });
        formData.append('user_id', userId);

        await api.post('/face/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      }

      setShowForm(false);
      fetchUsers();
      alert('Tạo người dùng thành công!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Lỗi');
    }
  };

  const handleUpdate = async (data, faceImages) => {
    try {
      // Update user info
      await api.put(`/users/${editUser.id}`, data);

      // Upload face images if provided
      if (faceImages && faceImages.length > 0) {
        const formData = new FormData();
        faceImages.forEach((blob, index) => {
          formData.append('images', blob, `face_${index}.jpg`);
        });
        formData.append('user_id', editUser.id);

        await api.post('/face/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      }

      setEditUser(null);
      setShowForm(false);
      fetchUsers();
      alert('Cập nhật người dùng thành công!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Lỗi');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Xác nhận xóa người dùng này?')) return;
    try {
      await api.delete(`/users/${id}`);
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Lỗi');
    }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Quản lý người dùng</h2>
        <button
          onClick={() => { setEditUser(null); setShowForm(true); }}
          className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
        >
          + Thêm người dùng
        </button>
      </div>

      {showForm && (
        <UserForm
          user={editUser}
          onSubmit={editUser ? handleUpdate : handleCreate}
          onCancel={() => { setShowForm(false); setEditUser(null); }}
        />
      )}

      <div className="bg-white rounded-xl shadow">
        <UserTable
          users={users}
          onEdit={(u) => { setEditUser(u); setShowForm(true); }}
          onDelete={handleDelete}
        />
      </div>
    </div>
  );
}
