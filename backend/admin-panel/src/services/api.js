const API_BASE = 'http://localhost:3000/api';

const getAuthHeaders = () => {
    const token = localStorage.getItem('adminToken');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
};

export const api = {
    // Auth
    login: async (email, password) => {
        const res = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    // Stats
    getStats: async () => {
        const res = await fetch(`${API_BASE}/admin/stats`, { headers: getAuthHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    // Lessons
    getLessons: async () => {
        const res = await fetch(`${API_BASE}/lessons`, { headers: getAuthHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    getLesson: async (id) => {
        const res = await fetch(`${API_BASE}/lessons/${id}`, { headers: getAuthHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    createLesson: async (lesson) => {
        const res = await fetch(`${API_BASE}/lessons`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(lesson)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    updateLesson: async (id, lesson) => {
        const res = await fetch(`${API_BASE}/lessons/${id}`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify(lesson)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    deleteLesson: async (id) => {
        const res = await fetch(`${API_BASE}/lessons/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    // Users
    getUsers: async () => {
        const res = await fetch(`${API_BASE}/admin/users`, { headers: getAuthHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    deleteUser: async (id) => {
        const res = await fetch(`${API_BASE}/admin/users/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    updateUserStatus: async (id, status) => {
        const res = await fetch(`${API_BASE}/admin/users/${id}/status`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({ status })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    updateUserRole: async (id, role) => {
        const res = await fetch(`${API_BASE}/admin/users/${id}/role`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({ role })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    resetUserPassword: async (id, newPassword) => {
        const res = await fetch(`${API_BASE}/admin/users/${id}/reset-password`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({ newPassword })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    },

    getUserProgress: async (id) => {
        const res = await fetch(`${API_BASE}/admin/users/${id}/progress`, { headers: getAuthHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        return data;
    }
};
