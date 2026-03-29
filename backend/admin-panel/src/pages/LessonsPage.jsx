import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

function LessonsPage() {
    const [lessons, setLessons] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [deleteId, setDeleteId] = useState(null);

    useEffect(() => {
        loadLessons();
    }, []);

    const loadLessons = async () => {
        try {
            const data = await api.getLessons();
            setLessons(data.lessons);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!deleteId) return;

        try {
            await api.deleteLesson(deleteId);
            setLessons(lessons.filter(l => l.id !== deleteId));
            setDeleteId(null);
        } catch (err) {
            setError(err.message);
        }
    };

    const getDifficultyBadge = (level) => {
        const badges = {
            beginner: { class: 'badge-success', text: '🌱 Sơ cấp' },
            intermediate: { class: 'badge-warning', text: '🌿 Trung cấp' },
            advanced: { class: 'badge-danger', text: '🌳 Nâng cao' }
        };
        const badge = badges[level] || badges.beginner;
        return <span className={`badge ${badge.class}`}>{badge.text}</span>;
    };

    if (loading) {
        return <div className="loading"><div className="spinner"></div></div>;
    }

    return (
        <div>
            <div className="page-header">
                <h1>📚 Quản lý bài học</h1>
                <Link to="/lessons/new" className="btn btn-primary">
                    + Thêm bài học
                </Link>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            {lessons.length === 0 ? (
                <div className="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    <p>Chưa có bài học nào</p>
                    <Link to="/lessons/new" className="btn btn-primary" style={{ marginTop: '1rem' }}>
                        Tạo bài học đầu tiên
                    </Link>
                </div>
            ) : (
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Tiêu đề</th>
                                <th>Nội dung</th>
                                <th>Cấp độ</th>
                                <th>Ngày tạo</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            {lessons.map((lesson) => (
                                <tr key={lesson.id}>
                                    <td>{lesson.id}</td>
                                    <td><strong>{lesson.title}</strong></td>
                                    <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {lesson.content}
                                    </td>
                                    <td>{getDifficultyBadge(lesson.difficulty_level)}</td>
                                    <td>{new Date(lesson.created_at).toLocaleDateString('vi-VN')}</td>
                                    <td>
                                        <div className="actions">
                                            <Link to={`/lessons/edit/${lesson.id}`} className="btn btn-sm btn-secondary">
                                                ✏️ Sửa
                                            </Link>
                                            <button
                                                onClick={() => setDeleteId(lesson.id)}
                                                className="btn btn-sm btn-danger"
                                            >
                                                🗑️ Xóa
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {deleteId && (
                <div className="modal-overlay">
                    <div className="modal">
                        <h2>⚠️ Xác nhận xóa</h2>
                        <p>Bạn có chắc chắn muốn xóa bài học này không?</p>
                        <div className="modal-actions">
                            <button onClick={() => setDeleteId(null)} className="btn btn-secondary">
                                Hủy
                            </button>
                            <button onClick={handleDelete} className="btn btn-danger">
                                Xóa
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default LessonsPage;
