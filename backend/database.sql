-- Create database
CREATE DATABASE IF NOT EXISTS speakwai_db;

-- Use the database
USE speakwai_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_email (email),
  INDEX idx_username (username)
);

-- Lessons table
CREATE TABLE IF NOT EXISTS lessons (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  content TEXT NOT NULL,
  difficulty_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_difficulty (difficulty_level),
  INDEX idx_created (created_at)
);

-- Insert sample lessons
INSERT INTO lessons (title, content, difficulty_level) VALUES
('Hello, how are you?', 'Learn basic greeting phrases', 'beginner'),
('I would like to order a coffee, please.', 'Practice ordering food and drinks', 'beginner'),
('What time is the next train?', 'Learn how to ask for directions and time', 'intermediate'),
('Can you help me find the nearest restaurant?', 'Practice asking for help and directions', 'intermediate'),
('Thank you very much for your help.', 'Learn expressions of gratitude', 'advanced');