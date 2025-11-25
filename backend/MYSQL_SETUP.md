# Hướng dẫn cài đặt MySQL cho SpeakWAI

## Phương pháp 1: Sử dụng XAMPP (Đơn giản nhất)

### 1. Tải và cài đặt XAMPP
1. Truy cập: https://www.apachefriends.org/en/xampp.html
2. Tải phiên bản phù hợp với hệ điều hành của bạn:
   - Windows: XAMPP for Windows
   - macOS: XAMPP for macOS
   - Linux: XAMPP for Linux

3. Chạy file installer và làm theo hướng dẫn

### 2. Cấu hình XAMPP
1. Mở XAMPP Control Panel
2. Khởi động Apache và MySQL
3. Kiểm tra:
   - Apache: http://localhost (phải hiện "Running")
   - MySQL: http://localhost/phpmyadmin (phải hiện "Running")

### 3. Tạo Database
1. Mở trình duyệt, truy cập: http://localhost/phpmyadmin
2. Đăng nhập với:
   - Server: localhost
   - Username: root
   - Password: (để trống khi cài đặt)

3. Chạy SQL queries:
```sql
CREATE DATABASE IF NOT EXISTS speakwai_db;
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
```

### 4. Cập nhật file .env trong backend
```bash
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=speakwai_db
DB_PORT=3306
```

## Phương pháp 2: Sử dụng Docker (Nâng cao)

### 1. Cài đặt Docker
1. Tải Docker Desktop từ: https://www.docker.com/products/docker-desktop/
2. Cài đặt và chạy Docker Desktop

### 2. Chạy MySQL container
```bash
docker run --name mysql -e MYSQL_ROOT_PASSWORD=password -p 3306:3306 -d mysql:8.0
```

### 3. Tạo Database và User
```bash
# Kết nối vào MySQL container
docker exec -it mysql mysql -u root -p

# Tạo database
CREATE DATABASE IF NOT EXISTS speakwai_db;

# Tạo user và cấp quyền
CREATE USER 'speakwai_user'@'%' IDENTIFIED BY 'your_mysql_password';
GRANT ALL PRIVILEGES ON speakwai_db.* TO 'speakwai_user'@'%';
FLUSH PRIVILEGES;
```

### 4. Import file database.sql
```bash
# Copy file SQL vào container
docker cp database.sql /tmp/
docker exec -i mysql mysql -u root -p speakwai_db < /tmp/database.sql
```

## Phương pháp 3: Sử dụng MySQL Cloud (Đơn giản)

### 1. Dịch vụ MySQL Cloud
1. Truy cập: https://mysql.com/
2. Đăng ký tài khoản miễn phí

### 2. Tạo Database
1. Sau khi đăng nhập, tạo database mới tên "speakwai_db"

### 3. Cấu hình kết nối
```bash
# Kết nối thông qua MySQL Shell hoặc sử dụng công cụ như MySQL Workbench
Host: [database-host].mysql.com
Port: 3306
User: [username]
Password: [password]
Database: speakwai_db
```

### 4. Import file database.sql
1. Sử dụng tab "Import" trong MySQL Cloud
2. Chọn file database.sql đã tạo ở trên

## Kiểm tra kết nối
Sau khi cài đặt, chạy backend server:
```bash
cd backend
npm start
```

Nếu server chạy thành công và kết nối được database, bạn sẽ thấy thông báo:
```
Server running on port 3000
Database connection successful
```

## Lưu ý quan trọng
1. **Bảo mật**: Không bao gồm thông tin nhạy cảm trong file .env hoặc commit lên Git
2. **Backup**: Thường xuyên backup database trước khi thực hiện các thay đổi
3. **CORS**: Backend đã được cấu hình CORS cho frontend
4. **JWT Secret**: Thay đổi secret key trong production

## Khắc phục sự cố thường gặp
1. **Lỗi kết nối database**: Kiểm tra lại thông tin đăng nhập MySQL
2. **Port conflict**: Đảm bảo port 3000 (backend) và 3306 (MySQL) không bị xung đột
3. **Permission denied**: Tạo user MySQL với quyền phù hợp
4. **Module not found**: Chạy `npm install` trong thư mục backend