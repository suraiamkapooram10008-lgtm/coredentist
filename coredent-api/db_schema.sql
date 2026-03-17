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
