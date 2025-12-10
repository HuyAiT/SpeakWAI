import { useState, useEffect } from 'react';
import { api } from '../services/api';

function UsersPage() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [modal, setModal] = useState({ type: null, user: null });
    const [newPassword, setNewPassword] = useState('');
    const [progressData, setProgressData] = useState(null);

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        try {
            const data = await api.getUsers();
            setUsers(data.users);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!modal.user) return;
        try {
            await api.deleteUser(modal.user.id);
            setUsers(users.filter(u => u.id !== modal.user.id));
            setModal({ type: null, user: null });
        } catch (err) {
            setError(err.message);
        }
    };

    const handleToggleStatus = async () => {
        if (!modal.user) return;
        const newStatus = modal.user.status === 'active' ? 'locked' : 'active';
        try {
            await api.updateUserStatus(modal.user.id, newStatus);
            setUsers(users.map(u => u.id === modal.user.id ? { ...u, status: newStatus } : u));
            setModal({ type: null, user: null });
        } catch (err) {
            setError(err.message);
        }
    };

    const handleToggleRole = async () => {
        if (!modal.user) return;
        const newRole = modal.user.role === 'admin' ? 'user' : 'admin';
        try {
            await api.updateUserRole(modal.user.id, newRole);
            setUsers(users.map(u => u.id === modal.user.id ? { ...u, role: newRole } : u));
            setModal({ type: null, user: null });
        } catch (err) {
            setError(err.message);
        }
    };

    const handleResetPassword = async () => {
        if (!modal.user || !newPassword) return;
        try {
            await api.resetUserPassword(modal.user.id, newPassword);
            setNewPassword('');
            setModal({ type: null, user: null });
            alert('Đã đặt lại mật khẩu thành công!');
        } catch (err) {
            setError(err.message);
        }
    };

    const handleViewProgress = async (user) => {
        try {
            const data = await api.getUserProgress(user.id);
            setProgressData({ user, ...data });
            setModal({ type: 'progress', user });
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) {
        return <div className="loading"><div className="spinner"></div></div>;
    }

    return (
        <div>
            <div className="page-header">
                <h1>👥 Quản lý người dùng</h1>
                <span className="badge badge-info">{users.length} người dùng</span>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Tên</th>
                            <th>Email</th>
                            <th>Vai trò</th>
                            <th>Trạng thái</th>
                            <th>Ngày tạo</th>
                            <th>Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map((user) => (
                            <tr key={user.id}>
                                <td>{user.id}</td>
                                <td><strong>{user.username}</strong></td>
                                <td>{user.email}</td>
                                <td>
                                    <span className={`badge ${user.role === 'admin' ? 'badge-secondary' : 'badge-primary'}`}>
                                        {user.role === 'admin' ? '👑 Admin' : '👤 User'}
                                    </span>
                                </td>
                                <td>
                                    <span className={`badge ${user.status === 'active' ? 'badge-success' : 'badge-danger'}`}>
                                        {user.status === 'active' ? '✅ Hoạt động' : '🔒 Đã khóa'}
                                    </span>
                                </td>
                                <td>{new Date(user.created_at).toLocaleDateString('vi-VN')}</td>
                                <td>
                                    <div className="actions" style={{ flexWrap: 'wrap' }}>
                                        <button
                                            onClick={() => handleViewProgress(user)}
                                            className="btn btn-sm btn-info"
                                            title="Xem tiến độ"
                                        >
                                            📊
                                        </button>
                                        <button
                                            onClick={() => setModal({ type: 'status', user })}
                                            className={`btn btn-sm ${user.status === 'active' ? 'btn-warning' : 'btn-primary'}`}
                                            title={user.status === 'active' ? 'Khóa' : 'Mở khóa'}
                                        >
                                            {user.status === 'active' ? '🔒' : '🔓'}
                                        </button>
                                        <button
                                            onClick={() => setModal({ type: 'role', user })}
                                            className="btn btn-sm btn-secondary"
                                            title="Đổi vai trò"
                                        >
                                            👑
                                        </button>
                                        <button
                                            onClick={() => setModal({ type: 'password', user })}
                                            className="btn btn-sm btn-secondary"
                                            title="Reset mật khẩu"
                                        >
                                            🔑
                                        </button>
                                        <button
                                            onClick={() => setModal({ type: 'delete', user })}
                                            className="btn btn-sm btn-danger"
                                            title="Xóa"
                                        >
                                            🗑️
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Delete Modal */}
            {modal.type === 'delete' && (
                <div className="modal-overlay">
                    <div className="modal">
                        <h2>⚠️ Xóa người dùng</h2>
                        <p>Bạn có chắc muốn xóa <strong>{modal.user.username}</strong>?</p>
                        <div className="modal-actions">
                            <button onClick={() => setModal({ type: null, user: null })} className="btn btn-secondary">Hủy</button>
                            <button onClick={handleDelete} className="btn btn-danger">Xóa</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Status Modal */}
            {modal.type === 'status' && (
                <div className="modal-overlay">
                    <div className="modal">
                        <h2>{modal.user.status === 'active' ? '🔒 Khóa tài khoản' : '🔓 Mở khóa tài khoản'}</h2>
                        <p>
                            {modal.user.status === 'active'
                                ? `Khóa tài khoản của ${modal.user.username}?`
                                : `Mở khóa tài khoản của ${modal.user.username}?`}
                        </p>
                        <div className="modal-actions">
                            <button onClick={() => setModal({ type: null, user: null })} className="btn btn-secondary">Hủy</button>
                            <button onClick={handleToggleStatus} className={`btn ${modal.user.status === 'active' ? 'btn-warning' : 'btn-primary'}`}>
                                {modal.user.status === 'active' ? 'Khóa' : 'Mở khóa'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Role Modal */}
            {modal.type === 'role' && (
                <div className="modal-overlay">
                    <div className="modal">
                        <h2>👑 Thay đổi vai trò</h2>
                        <p>
                            Đổi vai trò của <strong>{modal.user.username}</strong> từ
                            <strong> {modal.user.role}</strong> thành
                            <strong> {modal.user.role === 'admin' ? 'user' : 'admin'}</strong>?
                        </p>
                        <div className="modal-actions">
                            <button onClick={() => setModal({ type: null, user: null })} className="btn btn-secondary">Hủy</button>
                            <button onClick={handleToggleRole} className="btn btn-primary">Xác nhận</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Reset Password Modal */}
            {modal.type === 'password' && (
                <div className="modal-overlay">
                    <div className="modal">
                        <h2>🔑 Đặt lại mật khẩu</h2>
                        <p>Đặt mật khẩu mới cho <strong>{modal.user.username}</strong></p>
                        <div className="form-group">
                            <label>Mật khẩu mới</label>
                            <input
                                type="password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                placeholder="Nhập mật khẩu mới (ít nhất 6 ký tự)"
                                minLength={6}
                            />
                        </div>
                        <div className="modal-actions">
                            <button onClick={() => { setModal({ type: null, user: null }); setNewPassword(''); }} className="btn btn-secondary">Hủy</button>
                            <button onClick={handleResetPassword} className="btn btn-primary" disabled={newPassword.length < 6}>
                                Đặt lại
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Progress Modal */}
            {modal.type === 'progress' && progressData && (
                <div className="modal-overlay">
                    <div className="modal" style={{ maxWidth: '600px' }}>
                        <h2>📊 Tiến độ học của {progressData.user.username}</h2>

                        <div className="stats-grid" style={{ marginTop: '1rem' }}>
                            <div className="stat-card">
                                <div className="stat-info">
                                    <h3>{progressData.totals?.lessons_completed || 0}</h3>
                                    <p>Bài học hoàn thành</p>
                                </div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-info">
                                    <h3>{progressData.totals?.practice_days || 0}</h3>
                                    <p>Ngày luyện tập</p>
                                </div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-info">
                                    <h3>{progressData.totals?.vocabulary_learned || 0}</h3>
                                    <p>Từ vựng đã học</p>
                                </div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-info">
                                    <h3>{progressData.totals?.listening_completed || 0}</h3>
                                    <p>Bài nghe hoàn thành</p>
                                </div>
                            </div>
                        </div>

                        <div className="modal-actions">
                            <button onClick={() => { setModal({ type: null, user: null }); setProgressData(null); }} className="btn btn-secondary">
                                Đóng
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default UsersPage;
