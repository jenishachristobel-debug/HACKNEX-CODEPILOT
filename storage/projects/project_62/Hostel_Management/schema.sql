-- ==========================================================
-- Hostel Management System - Database Schema & Seed Data
-- Database: hostel_db
-- Target: MySQL 8.0+
-- ==========================================================

CREATE DATABASE IF NOT EXISTS hostel_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hostel_db;

-- 1. Admins Table
CREATE TABLE IF NOT EXISTS admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    role VARCHAR(50) DEFAULT 'Chief Warden',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Students Table
CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_number VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    department VARCHAR(100) NOT NULL,
    gender VARCHAR(20) NOT NULL,
    emergency_contact VARCHAR(100),
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. Rooms Table
CREATE TABLE IF NOT EXISTS rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(30) NOT NULL UNIQUE,
    block_name VARCHAR(50) NOT NULL,
    room_type VARCHAR(50) NOT NULL, -- 'Single', 'Double', 'Triple', 'Deluxe Suite'
    capacity INT NOT NULL DEFAULT 1,
    current_occupancy INT NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'Available', -- 'Available', 'Full', 'Maintenance'
    price_per_term DECIMAL(10, 2) DEFAULT 0.00,
    amenities TEXT
) ENGINE=InnoDB;

-- 4. Bookings Table (Allocation & History)
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    room_id INT NOT NULL,
    allocation_date DATE NOT NULL,
    vacate_date DATE NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Active', -- 'Active', 'Vacated', 'Cancelled'
    remarks TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_booking_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_booking_room FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Complaints Table
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    room_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'Electrical', 'Plumbing', 'Furniture', 'Cleanliness', 'Internet', 'Other'
    description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'Medium', -- 'Low', 'Medium', 'High', 'Urgent'
    date_raised DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending', -- 'Pending', 'In Progress', 'Resolved'
    admin_remarks TEXT,
    resolved_date DATETIME NULL,
    CONSTRAINT fk_complaint_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_complaint_room FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Indexing for high performance queries
CREATE INDEX idx_student_roll ON students(roll_number);
CREATE INDEX idx_student_email ON students(email);
CREATE INDEX idx_room_type ON rooms(room_type);
CREATE INDEX idx_room_status ON rooms(status);
CREATE INDEX idx_booking_status ON bookings(status);
CREATE INDEX idx_complaint_status ON complaints(status);
