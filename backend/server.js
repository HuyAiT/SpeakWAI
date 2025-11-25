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
  origin: ['http://localhost:8080', 'http://127.0.0.1:8080'], // Flutter web default port
  credentials: true
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

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

// Routes
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

        // Insert new user
        const insertQuery = 'INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, NOW())';
        db.query(insertQuery, [username, email, hash], (err, results) => {
          if (err) {
            console.error('Database error:', err);
            return res.status(500).json({ error: 'Database error' });
          }

          // Generate JWT token
          const token = jwt.sign(
            { id: results.insertId, username, email },
            JWT_SECRET,
            { expiresIn: '24h' }
          );

          res.status(201).json({
            message: 'User registered successfully',
            token,
            user: { id: results.insertId, username, email }
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

      // Compare password
      bcrypt.compare(password, user.password_hash, (err, isMatch) => {
        if (err) {
          console.error('Bcrypt error:', err);
          return res.status(500).json({ error: 'Error comparing password' });
        }

        if (!isMatch) {
          return res.status(401).json({ error: 'Invalid credentials' });
        }

        // Generate JWT token
        const token = jwt.sign(
          { id: user.id, username: user.username, email: user.email },
          JWT_SECRET,
          { expiresIn: '24h' }
        );

        res.json({
          message: 'Login successful',
          token,
          user: { id: user.id, username: user.username, email: user.email }
        });
      });
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Get lessons
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

// Get user profile
app.get('/api/profile', verifyToken, (req, res) => {
  try {
    const query = 'SELECT id, username, email, created_at FROM users WHERE id = ?';
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
          created_at: user.created_at
        }
      });
    });
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Something went wrong!',
    message: err.message
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  
  // Create database tables if they don't exist
  const createUsersTable = `
    CREATE TABLE IF NOT EXISTS users (
      id INT AUTO_INCREMENT PRIMARY KEY,
      username VARCHAR(50) UNIQUE NOT NULL,
      email VARCHAR(100) UNIQUE NOT NULL,
      password_hash VARCHAR(255) NOT NULL,
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

  db.query(createUsersTable);
  db.query(createLessonsTable);
  
  // Insert sample lessons
  const sampleLessons = [
    {
      title: 'Hello, how are you?',
      content: 'Learn basic greeting phrases',
      difficulty_level: 'beginner'
    },
    {
      title: 'I would like to order a coffee, please.',
      content: 'Practice ordering food and drinks',
      difficulty_level: 'beginner'
    },
    {
      title: 'What time is the next train?',
      content: 'Learn how to ask for directions and time',
      difficulty_level: 'intermediate'
    },
    {
      title: 'Can you help me find the nearest restaurant?',
      content: 'Practice asking for help and directions',
      difficulty_level: 'intermediate'
    },
    {
      title: 'Thank you very much for your help.',
      content: 'Learn expressions of gratitude',
      difficulty_level: 'advanced'
    }
  ];

  const insertSampleLessons = 'INSERT INTO lessons (title, content, difficulty_level) VALUES ?';
  sampleLessons.forEach(lesson => {
    db.query(insertSampleLessons, [lesson.title, lesson.content, lesson.difficulty_level]);
  });
});