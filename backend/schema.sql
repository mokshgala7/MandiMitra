-- ============================================================
-- MandiMitra MySQL Database Schema
-- Compatible with MySQL 8.0+ and MySQL Workbench
-- ============================================================

CREATE DATABASE IF NOT EXISTS mandimitra
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE mandimitra;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NULL,
    mobile VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    village VARCHAR(150) NULL,
    primary_crop VARCHAR(50) NOT NULL,
    latitude DECIMAL(10, 6) NULL,
    longitude DECIMAL(10, 6) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_mobile (mobile),
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. MANDIS MASTER TABLE
CREATE TABLE IF NOT EXISTS mandis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mandi_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    district VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    geocoding_source VARCHAR(50) DEFAULT 'osm_nominatim',
    geocoding_confidence VARCHAR(50) DEFAULT 'verified',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mandi_coords (latitude, longitude),
    INDEX idx_mandi_district (district),
    INDEX idx_mandi_state (state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. CROP PRICES TABLE
CREATE TABLE IF NOT EXISTS crop_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mandi_id VARCHAR(255) NOT NULL,
    crop VARCHAR(50) NOT NULL,
    variety VARCHAR(100) NOT NULL,
    grade VARCHAR(50) NOT NULL,
    price_date DATE NOT NULL,
    min_price DECIMAL(10, 2) NOT NULL,
    max_price DECIMAL(10, 2) NOT NULL,
    modal_price DECIMAL(10, 2) NOT NULL,
    price_unit VARCHAR(50) DEFAULT 'Rs./Quintal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_price_lookup (mandi_id, crop, price_date),
    INDEX idx_crop_date (crop, price_date),
    INDEX idx_mandi_crop (mandi_id, crop),
    CONSTRAINT fk_crop_prices_mandi FOREIGN KEY (mandi_id) REFERENCES mandis (mandi_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. SEARCH HISTORY TABLE
CREATE TABLE IF NOT EXISTS search_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    crop VARCHAR(50) NOT NULL,
    quantity_kg DECIMAL(10, 2) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    selected_mandi_id VARCHAR(255) NULL,
    has_middleman BOOLEAN DEFAULT FALSE,
    middleman_price DECIMAL(10, 2) NULL,
    middleman_commission DECIMAL(10, 2) NULL,
    middleman_other DECIMAL(10, 2) NULL,
    recommendation VARCHAR(50) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_search_user (user_id),
    INDEX idx_search_created (created_at),
    CONSTRAINT fk_search_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
