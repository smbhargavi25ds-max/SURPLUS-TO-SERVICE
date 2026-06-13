-   Run this in MySQL Workbench or CLI: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS surplus_service;
USE surplus_service;

CREATE TABLE IF NOT EXISTS users (
    
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    role ENUM('farmer','restaurant','ngo','composter','community_garden','individual') NOT NULL,
    password VARCHAR(255) NOT NULL,
    location VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS listings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category ENUM('produce','cooked','bakery','compost','seeds','other') NOT NULL,
    description VARCHAR(300) NOT NULL,
    quantity_kg DECIMAL(8,2) NOT NULL,
    expires_at DATETIME NOT NULL,
    pickup_pref ENUM('self_collect','i_deliver','either') DEFAULT 'self_collect',
    status ENUM('available','claimed','expired') DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS exchanges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    listing_id INT NOT NULL,
    donor_id INT NOT NULL,
    recipient_id INT NOT NULL,
    pickup_time VARCHAR(100),
    quantity_kg DECIMAL(8,2),
    status ENUM('pending','completed','cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id),
    FOREIGN KEY (donor_id) REFERENCES users(id),
    FOREIGN KEY (recipient_id) REFERENCES users(id)
);

-- Sample data
INSERT INTO users (name, email, role, password, location) VALUES
('Raju Krishnan', 'raju@farm.com', 'farmer', '$2b$12$placeholder', 'Devanahalli, Karnataka'),
('Green Leaf Restaurant', 'info@greenleaf.com', 'restaurant', '$2b$12$placeholder', 'Bangalore'),
('Annapoorna NGO', 'contact@annapoorna.org', 'ngo', '$2b$12$placeholder', 'Bangalore');

INSERT INTO listings (user_id, category, description, quantity_kg, expires_at, pickup_pref) VALUES
(1, 'produce', 'Mixed vegetables — fresh from farm', 15.00, DATE_ADD(NOW(), INTERVAL 8 HOUR), 'self_collect'),
(2, 'cooked', 'Dal & rice — 30 portions', 12.00, DATE_ADD(NOW(), INTERVAL 5 HOUR), 'i_deliver'),
(1, 'seeds', 'Tomato seeds — 200 packets', 2.00, DATE_ADD(NOW(), INTERVAL 7 DAY), 'either');


