-- ============================================================
-- REFLEX DELIVERY MANAGEMENT SYSTEM
-- PostgreSQL / Supabase Database Schema
-- ============================================================

-- ============================================================
-- USERS
-- Handles Retailer, Dispatcher and Rider accounts
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,

    name VARCHAR(100) NOT NULL,

    phone VARCHAR(20) NOT NULL UNIQUE,

    role VARCHAR(20) NOT NULL
        CHECK (role IN ('Retailer', 'Dispatcher', 'Rider')),

    password_hash TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- DELIVERIES
-- ============================================================

CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id SERIAL PRIMARY KEY,

    retailer_id INTEGER NOT NULL,

    rider_id INTEGER NULL,

    customer_name VARCHAR(100) NOT NULL,

    customer_phone VARCHAR(20) NOT NULL,

    delivery_address VARCHAR(255) NOT NULL,

    item_description TEXT NOT NULL,

    qr_code VARCHAR(64) NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'OPEN'
        CHECK (
            status IN (
                'OPEN',
                'ASSIGNED',
                'PICKED_UP',
                'DELIVERED'
            )
        ),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_delivery_retailer
        FOREIGN KEY (retailer_id)
        REFERENCES users(user_id),

    CONSTRAINT fk_delivery_rider
        FOREIGN KEY (rider_id)
        REFERENCES users(user_id)
);


-- ============================================================
-- STATUS HISTORY
-- Keeps track of delivery status changes
-- ============================================================

CREATE TABLE IF NOT EXISTS status_history (
    history_id SERIAL PRIMARY KEY,

    delivery_id INTEGER NOT NULL,

    status VARCHAR(20) NOT NULL,

    changed_by INTEGER NULL,

    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_status_delivery
        FOREIGN KEY (delivery_id)
        REFERENCES deliveries(delivery_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_status_user
        FOREIGN KEY (changed_by)
        REFERENCES users(user_id)
);


-- ============================================================
-- QR CONFIRMATIONS
-- Records QR delivery confirmation
-- ============================================================

CREATE TABLE IF NOT EXISTS qr_confirmations (
    confirmation_id SERIAL PRIMARY KEY,

    delivery_id INTEGER NOT NULL,

    rider_id INTEGER NOT NULL,

    result VARCHAR(20) NOT NULL,

    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_qr_delivery
        FOREIGN KEY (delivery_id)
        REFERENCES deliveries(delivery_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_qr_rider
        FOREIGN KEY (rider_id)
        REFERENCES users(user_id)
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_users_phone
    ON users(phone);

CREATE INDEX IF NOT EXISTS idx_users_role
    ON users(role);

CREATE INDEX IF NOT EXISTS idx_deliveries_status
    ON deliveries(status);

CREATE INDEX IF NOT EXISTS idx_deliveries_retailer
    ON deliveries(retailer_id);

CREATE INDEX IF NOT EXISTS idx_deliveries_rider
    ON deliveries(rider_id);

CREATE INDEX IF NOT EXISTS idx_status_delivery
    ON status_history(delivery_id);

CREATE INDEX IF NOT EXISTS idx_qr_delivery
    ON qr_confirmations(delivery_id);
