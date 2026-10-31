-- =====================================================================
-- Full Updated Database Schema: Daycare Childcare Management System
-- File: schema.sql
-- Compatible with PostgreSQL 13+
-- =====================================================================

-- 1. App Users & Roles (Managers & Teachers)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'teacher', -- 'manager' or 'teacher'
    full_name VARCHAR(120),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Classrooms & Cohorts
CREATE TABLE IF NOT EXISTS classrooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    age_group VARCHAR(60), -- e.g. 'Infant (0-1 yr)', 'Toddler (1-2.5 yrs)', 'Preschool (3-5 yrs)'
    target_ratio_child INTEGER DEFAULT 4, -- 1:4 default for toddlers
    max_capacity INTEGER DEFAULT 15,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Children Roster with Medical, Allergy & Classroom Tracking
CREATE TABLE IF NOT EXISTS children (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    date_of_birth DATE,
    classroom_id INTEGER REFERENCES classrooms(id) ON DELETE SET NULL,
    room_name VARCHAR(50) DEFAULT 'Toddler Room B',
    current_status VARCHAR(40) DEFAULT 'Checked Out', -- 'Checked In', 'Checked Out', 'Urgent Alert', 'Late Drop-Off'
    allergy_info TEXT DEFAULT NULL,                   -- e.g. 'Peanut Allergy (EpiPen in Room Safe)'
    dietary_restrictions TEXT DEFAULT NULL,          -- e.g. 'Lactose-Free Milk Only'
    emergency_notes TEXT DEFAULT NULL,               -- e.g. 'Inhaler in front cabinet'
    parent_first_name VARCHAR(80),
    parent_last_name VARCHAR(80),
    parent_phone VARCHAR(35) NOT NULL,
    preferred_channel VARCHAR(20) DEFAULT 'WhatsApp', -- 'WhatsApp' or 'SMS'
    last_status_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_action_by VARCHAR(80) DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Authorized Guardians & Chain of Custody
CREATE TABLE IF NOT EXISTS authorized_guardians (
    id SERIAL PRIMARY KEY,
    child_id INTEGER REFERENCES children(id) ON DELETE CASCADE,
    full_name VARCHAR(120) NOT NULL,
    relationship VARCHAR(50) NOT NULL, -- 'Mother', 'Father', 'Grandmother', 'Nanny'
    phone_number VARCHAR(35) NOT NULL,
    email VARCHAR(120) DEFAULT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    id_verified BOOLEAN DEFAULT TRUE,
    verification_pin VARCHAR(6) DEFAULT NULL,
    access_type VARCHAR(20) DEFAULT 'Permanent',
    pickup_expires_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    pickup_used_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    authorized_by VARCHAR(80) DEFAULT NULL,
    verification_attempts INTEGER DEFAULT 0,
    government_id_type VARCHAR(50) DEFAULT 'State Driver License',
    national_id_number VARCHAR(50) DEFAULT NULL,
    photo_url TEXT DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Daily Care Milestones & Incident Logs (Nap, Meal, Diaper, Incident)
CREATE TABLE IF NOT EXISTS daily_care_logs (
    id SERIAL PRIMARY KEY,
    child_id INTEGER REFERENCES children(id) ON DELETE CASCADE,
    teacher_username VARCHAR(80) NOT NULL,
    category VARCHAR(30) NOT NULL, -- 'meal', 'nap', 'diaper', 'incident', 'milestone'
    title VARCHAR(120) NOT NULL,
    details TEXT,
    metric_value VARCHAR(60), -- e.g. '100% finished', '1.5 hrs', 'Dry diaper', '40dB white noise'
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    parent_notified BOOLEAN DEFAULT FALSE,
    notification_channel VARCHAR(20) DEFAULT 'WhatsApp'
);

-- 6. Check-in & Check-out Hand-off Audits (Chain of Custody Handshake)
CREATE TABLE IF NOT EXISTS attendance_handshakes (
    id SERIAL PRIMARY KEY,
    child_id INTEGER REFERENCES children(id) ON DELETE CASCADE,
    action_type VARCHAR(20) NOT NULL, -- 'CHECK_IN' or 'CHECK_OUT'
    guardian_id INTEGER REFERENCES authorized_guardians(id) ON DELETE SET NULL,
    guardian_name_snapshot VARCHAR(120),
    teacher_username VARCHAR(80) NOT NULL,
    departure_notes TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Africa's Talking SMS & WhatsApp Inbound/Outbound Message Logs
CREATE TABLE IF NOT EXISTS message_logs (
    id SERIAL PRIMARY KEY,
    child_id INTEGER REFERENCES children(id) ON DELETE SET NULL,
    recipient_phone VARCHAR(35) NOT NULL,
    first_name VARCHAR(80),
    last_name VARCHAR(80),
    channel VARCHAR(20) NOT NULL DEFAULT 'SMS', -- 'SMS' or 'WhatsApp'
    direction VARCHAR(20) NOT NULL DEFAULT 'outbound', -- 'inbound' or 'outbound'
    message_body TEXT NOT NULL,
    delivery_status VARCHAR(30) DEFAULT 'Delivered', -- 'Delivered', 'Sent', 'Failed'
    at_message_id VARCHAR(100) DEFAULT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sample Data Insertion for Fast Testing
INSERT INTO classrooms (name, age_group, target_ratio_child, max_capacity)
VALUES 
    ('Toddler Room B', 'Toddler (1-2.5 yrs)', 4, 16),
    ('Infants A', 'Infants (0-1 yr)', 3, 8),
    ('Preschool B', 'Preschool (3-5 yrs)', 8, 20)
ON CONFLICT (name) DO NOTHING;
