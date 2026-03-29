import { useState, useEffect } from 'react';
import { api } from '../services/api';

function DashboardPage() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            const data = await api.getStats();
            setStats(data.stats);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="loading"><div className="spinner"></div></div>;
    }

    if (error) {
        return <div className="alert alert-error">{error}</div>;
    }

    return (
        <div>
            <div className="page-header">
                <h1>📊 Dashboard</h1>
            </div>

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon primary">👥</div>
                    <div className="stat-info">
                        <h3>{stats?.totalUsers || 0}</h3>
                        <p>Tổng người dùng</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon secondary">📚</div>
                    <div className="stat-info">
                        <h3>{stats?.totalLessons || 0}</h3>
                        <p>Tổng bài học</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon accent">✅</div>
                    <div className="stat-info">
                        <h3>{stats?.activeUsers || 0}</h3>
                        <p>Tài khoản hoạt động</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon info">🆕</div>
                    <div className="stat-info">
                        <h3>{stats?.newUsersToday || 0}</h3>
                        <p>Người dùng mới hôm nay</p>
                    </div>
                </div>
            </div>

            {/* Lessons by Level */}
            <div className="table-container" style={{ marginTop: '2rem' }}>
                <table>
                    <thead>
                        <tr>
                            <th>Cấp độ bài học</th>
                            <th>Số lượng</th>
                        </tr>
                    </thead>
                    <tbody>
                        {stats?.lessonsByLevel?.map((item) => (
                            <tr key={item.difficulty_level}>
                                <td>
                                    <span className={`badge ${item.difficulty_level === 'beginner' ? 'badge-success' :
                                            item.difficulty_level === 'intermediate' ? 'badge-warning' : 'badge-danger'
                                        }`}>
                                        {item.difficulty_level === 'beginner' ? '🌱 Sơ cấp' :
                                            item.difficulty_level === 'intermediate' ? '🌿 Trung cấp' : '🌳 Nâng cao'}
                                    </span>
                                </td>
                                <td>{item.count}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Quick Info */}
            <div style={{ marginTop: '2rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="stat-card">
                    <div className="stat-icon" style={{ background: 'rgba(239, 68, 68, 0.2)', color: 'var(--danger)' }}>🔒</div>
                    <div className="stat-info">
                        <h3>{stats?.lockedUsers || 0}</h3>
                        <p>Tài khoản bị khóa</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default DashboardPage;
