const express = require('express');
const mysql = require('mysql2');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const helmet = require('helmet');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors({
  origin: ['http://localhost:8080', 'http://127.0.0.1:8080', 'http://localhost:5173', 'http://127.0.0.1:5173'], // Flutter web + Vite admin
  credentials: true
}));
app.use(express.json({ limit: '50mb' }));  // Increased for audio base64
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Database connection
const db = mysql.createConnection({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'speakwai_db',
  port: process.env.DB_PORT || 3306
});

// JWT Secret
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production';

// Middleware for token verification
const verifyToken = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
};

// Middleware for admin verification
const verifyAdmin = (req, res, next) => {
  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Access denied. Admin only.' });
  }
  next();
};

// ==================== AUTH ROUTES ====================

// Register
app.post('/api/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;

    // Validation
    if (!username || !email || !password) {
      return res.status(400).json({ error: 'All fields are required' });
    }

    if (password.length < 6) {
      return res.status(400).json({ error: 'Password must be at least 6 characters' });
    }

    // Check if user already exists
    const checkUserQuery = 'SELECT id FROM users WHERE email = ? OR username = ?';
    db.query(checkUserQuery, [email, username], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (results.length > 0) {
        return res.status(400).json({ error: 'User already exists' });
      }

      // Hash password
      bcrypt.hash(password, 10, (err, hash) => {
        if (err) {
          console.error('Bcrypt error:', err);
          return res.status(500).json({ error: 'Error hashing password' });
        }

        // Insert new user (default role: user, status: active)
        const insertQuery = 'INSERT INTO users (username, email, password_hash, role, status, created_at) VALUES (?, ?, ?, ?, ?, NOW())';
        db.query(insertQuery, [username, email, hash, 'user', 'active'], (err, results) => {
          if (err) {
            console.error('Database error:', err);
            return res.status(500).json({ error: 'Database error' });
          }

          // Generate JWT token
          const token = jwt.sign(
            { id: results.insertId, username, email, role: 'user' },
            JWT_SECRET,
            { expiresIn: '24h' }
          );

          res.status(201).json({
            message: 'User registered successfully',
            token,
            user: { id: results.insertId, username, email, role: 'user' }
          });
        });
      });
    });
  } catch (error) {
    console.error('Register error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Login
app.post('/api/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    // Validation
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    // Find user
    const query = 'SELECT * FROM users WHERE email = ?';
    db.query(query, [email], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (results.length === 0) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      const user = results[0];

      // Check if account is locked
      if (user.status === 'locked') {
        return res.status(403).json({ error: 'Account is locked. Please contact admin.' });
      }

      // Compare password
      bcrypt.compare(password, user.password_hash, (err, isMatch) => {
        if (err) {
          console.error('Bcrypt error:', err);
          return res.status(500).json({ error: 'Error comparing password' });
        }

        if (!isMatch) {
          return res.status(401).json({ error: 'Invalid credentials' });
        }

        // Generate JWT token with role
        const token = jwt.sign(
          { id: user.id, username: user.username, email: user.email, role: user.role || 'user' },
          JWT_SECRET,
          { expiresIn: '24h' }
        );

        res.json({
          message: 'Login successful',
          token,
          user: { id: user.id, username: user.username, email: user.email, role: user.role || 'user' }
        });
      });
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Forgot Password
app.post('/api/forgot-password', async (req, res) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({ error: 'Email is required' });
    }

    // Check if user exists
    const query = 'SELECT id, username FROM users WHERE email = ?';
    db.query(query, [email], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (results.length === 0) {
        // Don't reveal if email exists or not for security
        return res.json({ message: 'If this email exists, a reset link has been sent.' });
      }

      // In production, send actual email with reset link
      // For now, just return success message
      console.log(`Password reset requested for: ${email}`);

      res.json({ message: 'If this email exists, a reset link has been sent.' });
    });
  } catch (error) {
    console.error('Forgot password error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// ==================== LESSONS ROUTES ====================

// Get all lessons
app.get('/api/lessons', verifyToken, (req, res) => {
  try {
    const query = 'SELECT * FROM lessons ORDER BY difficulty_level ASC, id ASC';
    db.query(query, (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      res.json({
        lessons: results,
        total: results.length
      });
    });
  } catch (error) {
    console.error('Get lessons error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Get single lesson by ID
app.get('/api/lessons/:id', verifyToken, (req, res) => {
  try {
    const { id } = req.params;
    const query = 'SELECT * FROM lessons WHERE id = ?';

    db.query(query, [id], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (results.length === 0) {
        return res.status(404).json({ error: 'Lesson not found' });
      }

      res.json({ lesson: results[0] });
    });
  } catch (error) {
    console.error('Get lesson error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Create lesson (Admin only)
app.post('/api/lessons', verifyToken, verifyAdmin, (req, res) => {
  try {
    const { title, content, difficulty_level } = req.body;

    if (!title || !content) {
      return res.status(400).json({ error: 'Title and content are required' });
    }

    const validLevels = ['beginner', 'intermediate', 'advanced'];
    const level = validLevels.includes(difficulty_level) ? difficulty_level : 'beginner';

    const query = 'INSERT INTO lessons (title, content, difficulty_level, created_at) VALUES (?, ?, ?, NOW())';
    db.query(query, [title, content, level], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      res.status(201).json({
        message: 'Lesson created successfully',
        lesson: { id: results.insertId, title, content, difficulty_level: level }
      });
    });
  } catch (error) {
    console.error('Create lesson error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Update lesson (Admin only)
app.put('/api/lessons/:id', verifyToken, verifyAdmin, (req, res) => {
  try {
    const { id } = req.params;
    const { title, content, difficulty_level } = req.body;

    if (!title || !content) {
      return res.status(400).json({ error: 'Title and content are required' });
    }

    const validLevels = ['beginner', 'intermediate', 'advanced'];
    const level = validLevels.includes(difficulty_level) ? difficulty_level : 'beginner';

    const query = 'UPDATE lessons SET title = ?, content = ?, difficulty_level = ? WHERE id = ?';
    db.query(query, [title, content, level, id], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (results.affectedRows === 0) {
        return res.status(404).json({ error: 'Lesson not found' });
      }

      res.json({
        message: 'Lesson updated successfully',
        lesson: { id: parseInt(id), title, content, difficulty_level: level }
      });
    });
  } catch (error) {
    console.error('Update lesson error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Delete lesson (Admin only)
app.delete('/api/lessons/:id', verifyToken, verifyAdmin, (req, res) => {
  try {
    const { id } = req.params;

    const query = 'DELETE FROM lessons WHERE id = ?';
    db.query(query, [id], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (results.affectedRows === 0) {
        return res.status(404).json({ error: 'Lesson not found' });
      }

      res.json({ message: 'Lesson deleted successfully' });
    });
  } catch (error) {
    console.error('Delete lesson error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// ==================== USER ROUTES ====================

// Get user profile
app.get('/api/profile', verifyToken, (req, res) => {
  try {
    const query = 'SELECT id, username, email, role, status, created_at FROM users WHERE id = ?';
    db.query(query, [req.user.id], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (results.length === 0) {
        return res.status(404).json({ error: 'User not found' });
      }

      const user = results[0];
      res.json({
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          role: user.role || 'user',
          created_at: user.created_at
        }
      });
    });
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Get user stats (for Flutter app)
app.get('/api/user/stats', verifyToken, (req, res) => {
  try {
    const userId = req.user.id;

    // Get user progress stats
    const statsQuery = `
      SELECT 
        COALESCE(SUM(lessons_completed), 0) as total_lessons_completed,
        COALESCE(SUM(practice_days), 0) as total_practice_days,
        COALESCE(SUM(vocabulary_learned), 0) as vocabulary_learned,
        COALESCE(SUM(listening_completed), 0) as listening_completed
      FROM user_progress 
      WHERE user_id = ?
    `;

    db.query(statsQuery, [userId], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        // Return default stats if table doesn't exist yet
        return res.json({
          stats: {
            lessons_completed: 0,
            practice_days: 0,
            vocabulary_learned: 0,
            listening_completed: 0
          }
        });
      }

      const stats = results[0] || {};
      res.json({
        stats: {
          lessons_completed: stats.total_lessons_completed || 0,
          practice_days: stats.total_practice_days || 0,
          vocabulary_learned: stats.vocabulary_learned || 0,
          listening_completed: stats.listening_completed || 0
        }
      });
    });
  } catch (error) {
    console.error('Get user stats error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Update user progress
app.post('/api/user/progress', verifyToken, (req, res) => {
  try {
    const userId = req.user.id;
    const { lesson_completed, vocabulary_learned, listening_completed } = req.body;

    // Get today's date
    const today = new Date().toISOString().split('T')[0];

    // Check if there's already a record for today
    const checkQuery = 'SELECT id FROM user_progress WHERE user_id = ? AND DATE(created_at) = ?';
    db.query(checkQuery, [userId, today], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (results.length > 0) {
        // Update existing record
        const updateQuery = `
          UPDATE user_progress SET 
            lessons_completed = lessons_completed + ?,
            vocabulary_learned = vocabulary_learned + ?,
            listening_completed = listening_completed + ?
          WHERE id = ?
        `;
        db.query(updateQuery, [
          lesson_completed || 0,
          vocabulary_learned || 0,
          listening_completed || 0,
          results[0].id
        ], (err) => {
          if (err) {
            console.error('Database error:', err);
            return res.status(500).json({ error: 'Database error' });
          }
          res.json({ message: 'Progress updated' });
        });
      } else {
        // Insert new record
        const insertQuery = `
          INSERT INTO user_progress (user_id, lessons_completed, vocabulary_learned, listening_completed, practice_days, created_at)
          VALUES (?, ?, ?, ?, 1, NOW())
        `;
        db.query(insertQuery, [
          userId,
          lesson_completed || 0,
          vocabulary_learned || 0,
          listening_completed || 0
        ], (err) => {
          if (err) {
            console.error('Database error:', err);
            return res.status(500).json({ error: 'Database error' });
          }
          res.json({ message: 'Progress recorded' });
        });
      }
    });
  } catch (error) {
    console.error('Update progress error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// ==================== ADMIN ROUTES ====================

// Get admin stats
app.get('/api/admin/stats', verifyToken, verifyAdmin, (req, res) => {
  try {
    const queries = {
      totalUsers: 'SELECT COUNT(*) as count FROM users',
      totalLessons: 'SELECT COUNT(*) as count FROM lessons',
      activeUsers: "SELECT COUNT(*) as count FROM users WHERE status = 'active'",
      lockedUsers: "SELECT COUNT(*) as count FROM users WHERE status = 'locked'",
      newUsersToday: 'SELECT COUNT(*) as count FROM users WHERE DATE(created_at) = CURDATE()',
      lessonsByLevel: 'SELECT difficulty_level, COUNT(*) as count FROM lessons GROUP BY difficulty_level'
    };

    const stats = {};
    let completed = 0;
    const total = Object.keys(queries).length;

    Object.entries(queries).forEach(([key, query]) => {
      db.query(query, (err, results) => {
        if (err) {
          console.error(`Error getting ${key}:`, err);
          stats[key] = key === 'lessonsByLevel' ? [] : 0;
        } else {
          stats[key] = key === 'lessonsByLevel' ? results : results[0].count;
        }

        completed++;
        if (completed === total) {
          res.json({ stats });
        }
      });
    });
  } catch (error) {
    console.error('Get admin stats error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Get all users (Admin only)
app.get('/api/admin/users', verifyToken, verifyAdmin, (req, res) => {
  try {
    const query = 'SELECT id, username, email, role, status, created_at FROM users ORDER BY created_at DESC';
    db.query(query, (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      res.json({
        users: results,
        total: results.length
      });
    });
  } catch (error) {
    console.error('Get users error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Delete user (Admin only)
app.delete('/api/admin/users/:id', verifyToken, verifyAdmin, (req, res) => {
  try {
    const { id } = req.params;

    // Prevent admin from deleting themselves
    if (parseInt(id) === req.user.id) {
      return res.status(400).json({ error: 'Cannot delete your own account' });
    }

    const query = 'DELETE FROM users WHERE id = ?';
    db.query(query, [id], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (results.affectedRows === 0) {
        return res.status(404).json({ error: 'User not found' });
      }

      res.json({ message: 'User deleted successfully' });
    });
  } catch (error) {
    console.error('Delete user error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Update user status (lock/unlock) (Admin only)
app.put('/api/admin/users/:id/status', verifyToken, verifyAdmin, (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    if (!['active', 'locked'].includes(status)) {
      return res.status(400).json({ error: 'Invalid status. Must be "active" or "locked"' });
    }

    // Prevent admin from locking themselves
    if (parseInt(id) === req.user.id) {
      return res.status(400).json({ error: 'Cannot change your own status' });
    }

    const query = 'UPDATE users SET status = ? WHERE id = ?';
    db.query(query, [status, id], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (results.affectedRows === 0) {
        return res.status(404).json({ error: 'User not found' });
      }

      res.json({ message: `User ${status === 'locked' ? 'locked' : 'unlocked'} successfully` });
    });
  } catch (error) {
    console.error('Update user status error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Update user role (Admin only)
app.put('/api/admin/users/:id/role', verifyToken, verifyAdmin, (req, res) => {
  try {
    const { id } = req.params;
    const { role } = req.body;

    if (!['user', 'admin'].includes(role)) {
      return res.status(400).json({ error: 'Invalid role. Must be "user" or "admin"' });
    }

    // Prevent admin from changing their own role
    if (parseInt(id) === req.user.id) {
      return res.status(400).json({ error: 'Cannot change your own role' });
    }

    const query = 'UPDATE users SET role = ? WHERE id = ?';
    db.query(query, [role, id], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (results.affectedRows === 0) {
        return res.status(404).json({ error: 'User not found' });
      }

      res.json({ message: `User role changed to ${role} successfully` });
    });
  } catch (error) {
    console.error('Update user role error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Reset user password (Admin only)
app.put('/api/admin/users/:id/reset-password', verifyToken, verifyAdmin, (req, res) => {
  try {
    const { id } = req.params;
    const { newPassword } = req.body;

    if (!newPassword || newPassword.length < 6) {
      return res.status(400).json({ error: 'New password must be at least 6 characters' });
    }

    bcrypt.hash(newPassword, 10, (err, hash) => {
      if (err) {
        console.error('Bcrypt error:', err);
        return res.status(500).json({ error: 'Error hashing password' });
      }

      const query = 'UPDATE users SET password_hash = ? WHERE id = ?';
      db.query(query, [hash, id], (err, results) => {
        if (err) {
          console.error('Database error:', err);
          return res.status(500).json({ error: 'Database error' });
        }

        if (results.affectedRows === 0) {
          return res.status(404).json({ error: 'User not found' });
        }

        res.json({ message: 'Password reset successfully' });
      });
    });
  } catch (error) {
    console.error('Reset password error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Get user progress (Admin only)
app.get('/api/admin/users/:id/progress', verifyToken, verifyAdmin, (req, res) => {
  try {
    const { id } = req.params;

    const query = `
      SELECT 
        up.*,
        u.username,
        u.email
      FROM user_progress up
      JOIN users u ON up.user_id = u.id
      WHERE up.user_id = ?
      ORDER BY up.created_at DESC
      LIMIT 30
    `;

    db.query(query, [id], (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      // Calculate totals
      const totals = results.reduce((acc, row) => ({
        lessons_completed: acc.lessons_completed + (row.lessons_completed || 0),
        vocabulary_learned: acc.vocabulary_learned + (row.vocabulary_learned || 0),
        listening_completed: acc.listening_completed + (row.listening_completed || 0),
        practice_days: acc.practice_days + (row.practice_days || 0)
      }), { lessons_completed: 0, vocabulary_learned: 0, listening_completed: 0, practice_days: 0 });

      res.json({
        progress: results,
        totals
      });
    });
  } catch (error) {
    console.error('Get user progress error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// ==================== AI PRONUNCIATION SCORING ====================

const multer = require('multer');
const FormData = require('form-data');
const axios = require('axios');

// Configure multer for audio file uploads
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB max
  fileFilter: (req, file, cb) => {
    // Accept audio files
    if (file.mimetype.startsWith('audio/')) {
      cb(null, true);
    } else {
      cb(new Error('Only audio files are allowed'), false);
    }
  }
});

// AI Server URL (Python FastAPI server)
const AI_SERVER_URL = process.env.AI_SERVER_URL || 'http://localhost:8000';

// Health check for AI server
app.get('/api/ai/health', async (req, res) => {
  try {
    const response = await axios.get(`${AI_SERVER_URL}/health`, { timeout: 5000 });
    res.json({
      ai_server: 'connected',
      model_loaded: response.data.model_loaded,
      device: response.data.device
    });
  } catch (error) {
    res.json({
      ai_server: 'disconnected',
      error: error.message
    });
  }
});

// Score pronunciation from audio file
app.post('/api/ai/score', verifyToken, upload.single('audio'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No audio file provided' });
    }

    // Get expected text (optional)
    const expectedText = req.body.text || '';

    // Create form data for AI server
    const formData = new FormData();
    formData.append('audio', req.file.buffer, {
      filename: 'recording.wav',
      contentType: req.file.mimetype
    });
    formData.append('text', expectedText);

    // Send to AI server
    const response = await axios.post(`${AI_SERVER_URL}/score`, formData, {
      headers: formData.getHeaders(),
      timeout: 30000 // 30 seconds timeout
    });

    // Return scores with user info
    res.json({
      success: true,
      user_id: req.user.id,
      scores: response.data.scores,
      feedback: response.data.feedback,
      expected_text: expectedText
    });

  } catch (error) {
    console.error('AI Scoring error:', error.message);

    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({
        error: 'AI server not available',
        message: 'Please make sure the AI server is running on port 8000'
      });
    }

    res.status(500).json({
      error: 'Scoring failed',
      message: error.response?.data?.detail || error.message
    });
  }
});

// Score pronunciation from base64 audio (for Flutter app)
app.post('/api/ai/score-base64', verifyToken, async (req, res) => {
  try {
    const { audio, text } = req.body;

    if (!audio) {
      return res.status(400).json({ error: 'No audio data provided' });
    }

    // Send to AI server
    const response = await axios.post(`${AI_SERVER_URL}/score-base64`, {
      audio: audio,
      text: text || ''
    }, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 30000
    });

    // Return scores
    res.json({
      success: true,
      user_id: req.user.id,
      scores: response.data.scores,
      feedback: response.data.feedback,
      expected_text: text
    });

  } catch (error) {
    console.error('AI Scoring error:', error.message);

    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({
        error: 'AI server not available',
        message: 'Please make sure the AI server is running on port 8000'
      });
    }

    res.status(500).json({
      error: 'Scoring failed',
      message: error.response?.data?.detail || error.message
    });
  }
});

// ==================== ERROR HANDLING ====================

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Something went wrong!',
    message: err.message
  });
});

// ==================== SERVER STARTUP ====================

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);

  // Create database tables if they don't exist
  const createUsersTable = `
    CREATE TABLE IF NOT EXISTS users (
      id INT AUTO_INCREMENT PRIMARY KEY,
      username VARCHAR(50) UNIQUE NOT NULL,
      email VARCHAR(100) UNIQUE NOT NULL,
      password_hash VARCHAR(255) NOT NULL,
      role ENUM('user', 'admin') DEFAULT 'user',
      status ENUM('active', 'locked') DEFAULT 'active',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `;

  const createLessonsTable = `
    CREATE TABLE IF NOT EXISTS lessons (
      id INT AUTO_INCREMENT PRIMARY KEY,
      title VARCHAR(200) NOT NULL,
      content TEXT NOT NULL,
      difficulty_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `;

  const createUserProgressTable = `
    CREATE TABLE IF NOT EXISTS user_progress (
      id INT AUTO_INCREMENT PRIMARY KEY,
      user_id INT NOT NULL,
      lessons_completed INT DEFAULT 0,
      vocabulary_learned INT DEFAULT 0,
      listening_completed INT DEFAULT 0,
      practice_days INT DEFAULT 0,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
  `;

  // Add role and status columns to existing users table if they don't exist
  const addRoleColumn = `
    ALTER TABLE users ADD COLUMN IF NOT EXISTS role ENUM('user', 'admin') DEFAULT 'user'
  `;

  const addStatusColumn = `
    ALTER TABLE users ADD COLUMN IF NOT EXISTS status ENUM('active', 'locked') DEFAULT 'active'
  `;

  db.query(createUsersTable);
  db.query(createLessonsTable);
  db.query(createUserProgressTable, (err) => {
    if (err && !err.message.includes('already exists')) {
      console.error('Error creating user_progress table:', err);
    }
  });

  // Try to add columns (will fail silently if they exist)
  db.query(addRoleColumn, (err) => {
    if (err && !err.message.includes('Duplicate')) {
      // Column might already exist or different error
    }
  });
  db.query(addStatusColumn, (err) => {
    if (err && !err.message.includes('Duplicate')) {
      // Column might already exist or different error
    }
  });

  // Create default admin user if no admin exists
  const checkAdminQuery = "SELECT id FROM users WHERE role = 'admin' LIMIT 1";
  db.query(checkAdminQuery, (err, results) => {
    if (err) {
      console.error('Error checking for admin:', err);
      return;
    }

    if (results.length === 0) {
      // Create default admin
      bcrypt.hash('admin123', 10, (err, hash) => {
        if (err) {
          console.error('Error creating admin:', err);
          return;
        }

        const insertAdmin = `
          INSERT INTO users (username, email, password_hash, role, status, created_at)
          VALUES ('admin', 'admin@speakwai.com', ?, 'admin', 'active', NOW())
          ON DUPLICATE KEY UPDATE role = 'admin'
        `;
        db.query(insertAdmin, [hash], (err) => {
          if (err) {
            console.error('Error inserting admin:', err);
          } else {
            console.log('Default admin created: admin@speakwai.com / admin123');
          }
        });
      });
    }
  });

  // Insert sample lessons only if table is empty
  db.query('SELECT COUNT(*) as count FROM lessons', (err, results) => {
    if (err) {
      console.error('Error checking lessons table:', err);
      return;
    }

    // Only insert if table is empty
    if (results[0].count === 0) {
      const sampleLessons = [
        ['Hello, how are you?', 'Learn basic greeting phrases', 'beginner'],
        ['I would like to order a coffee, please.', 'Practice ordering food and drinks', 'beginner'],
        ['What time is the next train?', 'Learn how to ask for directions and time', 'intermediate'],
        ['Can you help me find the nearest restaurant?', 'Practice asking for help and directions', 'intermediate'],
        ['Thank you very much for your help.', 'Learn expressions of gratitude', 'advanced']
      ];

      const insertQuery = 'INSERT INTO lessons (title, content, difficulty_level) VALUES (?, ?, ?)';
      sampleLessons.forEach(lesson => {
        db.query(insertQuery, lesson, (err) => {
          if (err) console.error('Error inserting lesson:', err);
        });
      });
      console.log('Sample lessons inserted successfully');
    }
  });
});