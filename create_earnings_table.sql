-- Create earnings_management table
-- Run this in your MySQL database

CREATE TABLE IF NOT EXISTS earnings_management (
    id INT AUTO_INCREMENT PRIMARY KEY,
    delivery_guy_id INT NOT NULL,
    payment_type VARCHAR(20) NOT NULL,
    amount FLOAT NOT NULL,
    payment_period VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    description TEXT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    admin_notes TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    approved_at DATETIME NULL,
    approved_by INT NULL,
    paid_at DATETIME NULL,
    
    INDEX idx_delivery_guy_id (delivery_guy_id),
    INDEX idx_payment_type (payment_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_start_date (start_date)
);

-- Add foreign key constraints if the tables exist
-- ALTER TABLE earnings_management 
-- ADD CONSTRAINT fk_earnings_delivery_guy 
-- FOREIGN KEY (delivery_guy_id) REFERENCES delivery_onboarding(id);

-- ALTER TABLE earnings_management 
-- ADD CONSTRAINT fk_earnings_approved_by 
-- FOREIGN KEY (approved_by) REFERENCES admin(id);
