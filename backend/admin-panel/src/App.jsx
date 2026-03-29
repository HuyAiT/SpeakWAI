import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import LessonsPage from './pages/LessonsPage';
import LessonFormPage from './pages/LessonFormPage';
import UsersPage from './pages/UsersPage';
import Layout from './components/Layout';
import './App.css';

// Auth context
const isAuthenticated = () => {
  const token = localStorage.getItem('adminToken');
  const user = JSON.parse(localStorage.getItem('adminUser') || '{}');
  return token && user.role === 'admin';
};

function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  const [authState, setAuthState] = useState(isAuthenticated());

  useEffect(() => {
    const checkAuth = () => setAuthState(isAuthenticated());
    window.addEventListener('storage', checkAuth);
    return () => window.removeEventListener('storage', checkAuth);
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage onLogin={() => setAuthState(true)} />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout onLogout={() => setAuthState(false)} />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="lessons" element={<LessonsPage />} />
          <Route path="lessons/new" element={<LessonFormPage />} />
          <Route path="lessons/edit/:id" element={<LessonFormPage />} />
          <Route path="users" element={<UsersPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
