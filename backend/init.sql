-- Digital Bank Pro - Database Initialization Script
-- This script creates necessary extensions and sets up initial data

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create a default admin user for testing
-- Email: admin@digitalbank.com
-- Password: Admin123!
INSERT INTO users (
    id,
    email,
    password_hash,
    full_name,
    phone,
    role,
    kyc_level,
    kyc_status,
    is_active,
    created_at
) VALUES (
    gen_random_uuid(),
    'admin@digitalbank.com',
    crypt('Admin123!', gen_salt('bf', 12)),
    'System Administrator',
    '+1 800 000 0000',
    'admin',
    3,
    'approved',
    true,
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Create a test customer for testing
-- Email: customer@digitalbank.com
-- Password: Customer123!
INSERT INTO users (
    id,
    email,
    password_hash,
    full_name,
    phone,
    role,
    kyc_level,
    kyc_status,
    is_active,
    created_at
) VALUES (
    gen_random_uuid(),
    'customer@digitalbank.com',
    crypt('Customer123!', gen_salt('bf', 12)),
    'John Customer',
    '+1 555 123 4567',
    'customer',
    2,
    'approved',
    true,
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Note: Accounts will be created via the API