CREATE DATABASE IF NOT EXISTS reflex_db;

USE reflex_db;

-- Retailers who create delivery requests
CREATE TABLE IF NOT EXISTS retailers (
    retailer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Riders who receive delivery assignments
CREATE TABLE IF NOT EXISTS riders (
    rider_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Delivery requests
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id INT AUTO_INCREMENT PRIMARY KEY,

    retailer_id INT NOT NULL,
    rider_id INT NULL,

    customer_name VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    delivery_address VARCHAR(255) NOT NULL,
    item_description TEXT NOT NULL,

    status ENUM(
        'Pending',
        'Assigned',
        'Picked Up',
        'Delivered'
    ) DEFAULT 'Pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (retailer_id)
        REFERENCES retailers(retailer_id),

    FOREIGN KEY (rider_id)
        REFERENCES riders(rider_id)
);-- Add QR code support to deliveries
ALTER TABLE deliveries
    ADD COLUMN qr_code VARCHAR(64) NULL,
    ADD COLUMN qr_scanned_at TIMESTAMP NULL;
