import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../services/api';

function LessonFormPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const isEdit = Boolean(id);

    const [form, setForm] = useState({
        title: '',
        content: '',
        difficulty_level: 'beginner'
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (isEdit) {
            loadLesson();
        }
    }, [id]);

    const loadLesson = async () => {
        try {
            setLoading(true);
            const data = await api.getLesson(id);
            setForm({
                title: data.lesson.title,
                content: data.lesson.content,
                difficulty_level: data.lesson.difficulty_level
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (isEdit) {
                await api.updateLesson(id, form);
            } else {
                await api.createLesson(form);
            }
            navigate('/lessons');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        setForm({ ...form, [e.target.name]: e.target.value });
    };

    if (loading && isEdit) {
        return <div className="loading"><div className="spinner"></div></div>;
    }

    return (
        <div>
            <div className="page-header">
                <h1>{isEdit ? '✏️ Sửa bài học' : '➕ Thêm bài học mới'}</h1>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="table-container" style={{ padding: '2rem' }}>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Tiêu đề (Câu để luyện nói)</label>
                        <input
                            type="text"
                            name="title"
                            value={form.title}
                            onChange={handleChange}
                            placeholder="Ví dụ: Hello, how are you today?"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Nội dung / Mô tả</label>
                        <textarea
                            name="content"
                            value={form.content}
                            onChange={handleChange}
                            placeholder="Mô tả bài học hoặc gợi ý cho người học..."
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Cấp độ</label>
                        <select
                            name="difficulty_level"
                            value={form.difficulty_level}
                            onChange={handleChange}
                        >
                            <option value="beginner">🌱 Sơ cấp (Beginner)</option>
                            <option value="intermediate">🌿 Trung cấp (Intermediate)</option>
                            <option value="advanced">🌳 Nâng cao (Advanced)</option>
                        </select>
                    </div>

                    <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? 'Đang lưu...' : (isEdit ? 'Cập nhật' : 'Tạo bài học')}
                        </button>
                        <button type="button" onClick={() => navigate('/lessons')} className="btn btn-secondary">
                            Hủy
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default LessonFormPage;
