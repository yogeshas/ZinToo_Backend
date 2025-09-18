-- Database Migration: Add Push Notification Fields to delivery_guy_auth table
-- Run this SQL command in your MySQL database

ALTER TABLE delivery_guy_auth 
ADD COLUMN device_token VARCHAR(500) NULL,
ADD COLUMN platform VARCHAR(20) NULL,
ADD COLUMN sns_endpoint_arn VARCHAR(500) NULL,
ADD COLUMN is_notifications_enabled BOOLEAN DEFAULT TRUE;

-- Verify the changes
DESCRIBE delivery_guy_auth;
