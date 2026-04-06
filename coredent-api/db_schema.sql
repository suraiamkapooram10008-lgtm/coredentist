-- Database schema for CoreDent API (Supabase compatible)
-- This file defines the tables used by the FastAPI backend.

CREATE TABLE IF NOT EXISTS "user" (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    practice_id UUID NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "patient" (
    id UUID PRIMARY KEY,
    practice_id UUID NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "appointment" (
    id UUID PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES "patient"(id) ON DELETE CASCADE,
    practitioner_id UUID NOT NULL REFERENCES "user"(id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "audit" (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES "user"(id),
    action VARCHAR(255) NOT NULL,
    entity VARCHAR(255),
    entity_id UUID,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- Additional tables (billing, clinical, etc.) can be added similarly.

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_email ON "user" (email);
CREATE INDEX IF NOT EXISTS idx_patient_practice ON "patient" (practice_id);
CREATE INDEX IF NOT EXISTS idx_appointment_practitioner ON "appointment" (practitioner_id);

-- Password Reset Tokens (for HIPAA-compliant password resets)
CREATE TABLE IF NOT EXISTS "password_reset_token" (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_password_reset_token ON "password_reset_token"(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_user ON "password_reset_token"(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_active ON "password_reset_token"(is_used, expires_at);

-- User Sessions (for JWT refresh token management)
CREATE TABLE IF NOT EXISTS "session" (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    refresh_token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_session_user ON "session"(user_id);
CREATE INDEX IF NOT EXISTS idx_session_refresh_token ON "session"(refresh_token);
CREATE INDEX IF NOT EXISTS idx_session_expires ON "session"(expires_at);

-- Audit Log (HIPAA compliance - track all access and modifications)
CREATE TABLE IF NOT EXISTS "audit_log" (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES "user"(id),
    action VARCHAR(255) NOT NULL,
    entity VARCHAR(255),
    entity_id UUID,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON "audit_log"(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON "audit_log"(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON "audit_log"(entity, entity_id);