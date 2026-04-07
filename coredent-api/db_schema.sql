-- CoreDent PMS - Complete Database Schema
-- Auto-generated from SQLAlchemy models
-- Compatible with PostgreSQL and Supabase
-- Last updated: 2026-04-07

-- ============================================
-- CORE TABLES
-- ============================================

-- Practices (multi-tenant support)
CREATE TABLE IF NOT EXISTS practices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    address_city VARCHAR(100),
    address_state VARCHAR(100),
    address_zip VARCHAR(20),
    country VARCHAR(100) DEFAULT 'US',
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    logo_url TEXT,
    license_number VARCHAR(100),
    tax_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'active',
    subscription_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_practice_active ON practices(is_active);

-- Users (staff members)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL, -- owner, admin, dentist, hygienist, front_desk, group_owner, group_admin
    practice_id UUID NOT NULL REFERENCES practices(id),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    password_changed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_practice_role ON users(practice_id, role);
CREATE INDEX IF NOT EXISTS idx_user_practice_active ON users(practice_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);

-- Password reset tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_password_reset_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_user ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_active ON password_reset_tokens(is_used, expires_at);

-- User sessions (JWT refresh token management)
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_session_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_session_refresh_token ON sessions(refresh_token);
CREATE INDEX IF NOT EXISTS idx_session_expires ON sessions(expires_at);

-- Audit logs (HIPAA compliance)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    changes JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);

-- ============================================
-- PATIENT MANAGEMENT
-- ============================================

-- Patients
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_id UUID NOT NULL REFERENCES practices(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10), -- male, female, other
    email VARCHAR(255),
    phone VARCHAR(20),
    address_street VARCHAR(255),
    address_city VARCHAR(100),
    address_state VARCHAR(100),
    address_zip VARCHAR(20),
    abha_id VARCHAR(20), -- India's ABHA ID
    ssn_last_four VARCHAR(4), -- US PHI
    emergency_contact JSONB, -- {name, relationship, phone}
    medical_alerts JSONB DEFAULT '[]',
    medical_history JSONB DEFAULT '{}',
    dental_history JSONB DEFAULT '{}',
    insurance_info JSONB,
    status VARCHAR(20) DEFAULT 'active', -- active, inactive
    consent_recorded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patient_practice_status ON patients(practice_id, status);
CREATE INDEX IF NOT EXISTS idx_patient_name ON patients(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_patient_practice_email ON patients(practice_id, email);
CREATE INDEX IF NOT EXISTS idx_patient_phone ON patients(phone);
CREATE INDEX IF NOT EXISTS idx_patient_abha_id ON patients(abha_id);

-- ============================================
-- APPOINTMENTS & SCHEDULING
-- ============================================

-- Appointment types
CREATE TABLE IF NOT EXISTS appointment_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    duration INTEGER NOT NULL DEFAULT 30,
    color VARCHAR(7) DEFAULT '#3B82F6',
    description TEXT,
    practice_id UUID REFERENCES practices(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chairs
CREATE TABLE IF NOT EXISTS chairs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    practice_id UUID NOT NULL REFERENCES practices(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chair_practice ON chairs(practice_id);

-- Appointments
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    provider_id UUID NOT NULL REFERENCES users(id),
    chair_id UUID REFERENCES chairs(id),
    appointment_type_id UUID REFERENCES appointment_types(id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'scheduled', -- scheduled, confirmed, in_progress, completed, cancelled, no_show
    type VARCHAR(50) DEFAULT 'in-office', -- in-office, telehealth, external
    notes TEXT,
    reminder_sent BOOLEAN DEFAULT FALSE,
    reminder_sent_at TIMESTAMP,
    confirmed_at TIMESTAMP,
    cancellation_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_appointment_provider ON appointments(provider_id);
CREATE INDEX IF NOT EXISTS idx_appointment_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointment_start_time ON appointments(start_time);
CREATE INDEX IF NOT EXISTS idx_appointment_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointment_practice_date ON appointments(start_time, status);

-- ============================================
-- CLINICAL
-- ============================================

-- Clinical notes
CREATE TABLE IF NOT EXISTS clinical_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    provider_id UUID NOT NULL REFERENCES users(id),
    appointment_id UUID REFERENCES appointments(id),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    note_type VARCHAR(50) DEFAULT 'general', -- general, progress, consultation, referral
    status VARCHAR(30) DEFAULT 'draft', -- draft, signed, locked
    signed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clinical_note_patient ON clinical_notes(patient_id);
CREATE INDEX IF NOT EXISTS idx_clinical_note_provider ON clinical_notes(provider_id);
CREATE INDEX IF NOT EXISTS idx_clinical_note_status ON clinical_notes(status);

-- Dental charts
CREATE TABLE IF NOT EXISTS dental_charts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE UNIQUE,
    chart_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Perio charts
CREATE TABLE IF NOT EXISTS perio_charts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    chart_date DATE NOT NULL,
    readings JSONB,
    notes TEXT,
    provider_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_perio_chart_patient ON perio_charts(patient_id);
CREATE INDEX IF NOT EXISTS idx_perio_chart_date ON perio_charts(chart_date);

-- ============================================
-- TREATMENT PLANS
-- ============================================

-- Treatment plans
CREATE TABLE IF NOT EXISTS treatment_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    provider_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(30) DEFAULT 'draft', -- draft, pending_approval, approved, in_progress, completed, rejected
    total_cost DECIMAL(10, 2),
    approved_cost DECIMAL(10, 2),
    start_date DATE,
    estimated_completion_date DATE,
    actual_completion_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_treatment_plan_patient ON treatment_plans(patient_id);
CREATE INDEX IF NOT EXISTS idx_treatment_plan_status ON treatment_plans(status);

-- Treatment phases
CREATE TABLE IF NOT EXISTS treatment_phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    treatment_plan_id UUID NOT NULL REFERENCES treatment_plans(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    sequence_number INTEGER,
    status VARCHAR(30) DEFAULT 'pending',
    estimated_cost DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_treatment_phase_plan ON treatment_phases(treatment_plan_id);

-- Treatment procedures
CREATE TABLE IF NOT EXISTS treatment_procedures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase_id UUID REFERENCES treatment_phases(id) ON DELETE CASCADE,
    treatment_plan_id UUID REFERENCES treatment_plans(id) ON DELETE CASCADE,
    tooth_number VARCHAR(10),
    tooth_surface VARCHAR(50),
    procedure_code VARCHAR(20),
    procedure_name VARCHAR(255) NOT NULL,
    description TEXT,
    cost DECIMAL(10, 2),
    status VARCHAR(30) DEFAULT 'pending', -- pending, in_progress, completed, skipped
    notes TEXT,
    sequence_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_treatment_procedure_plan ON treatment_procedures(treatment_plan_id);

-- Procedure library
CREATE TABLE IF NOT EXISTS procedure_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    default_cost DECIMAL(10, 2),
    default_duration INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_procedure_library_code ON procedure_library(code);

-- Treatment plan templates
CREATE TABLE IF NOT EXISTS treatment_plan_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_data JSONB,
    practice_id UUID REFERENCES practices(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Treatment plan notes
CREATE TABLE IF NOT EXISTS treatment_plan_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    treatment_plan_id UUID NOT NULL REFERENCES treatment_plans(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_treatment_plan_note ON treatment_plan_notes(treatment_plan_id);

-- ============================================
-- BILLING
-- ============================================

-- Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    treatment_plan_id UUID REFERENCES treatment_plans(id),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL DEFAULT 0,
    tax DECIMAL(10, 2) DEFAULT 0,
    discount DECIMAL(10, 2) DEFAULT 0,
    total DECIMAL(10, 2) NOT NULL DEFAULT 0,
    amount_paid DECIMAL(10, 2) DEFAULT 0,
    balance_due DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(30) DEFAULT 'draft', -- draft, sent, paid, overdue, cancelled, refunded
    due_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_invoice_patient ON invoices(patient_id);
CREATE INDEX IF NOT EXISTS idx_invoice_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoice_number ON invoices(invoice_number);

-- Payments
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id),
    payment_number VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(30) NOT NULL, -- cash, credit, debit, check, insurance, financing
    payment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reference_number VARCHAR(100),
    notes TEXT,
    status VARCHAR(30) DEFAULT 'completed', -- pending, completed, failed, refunded, chargeback
    refunded_at TIMESTAMP,
    refunded_amount DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_patient ON payments(patient_id);
CREATE INDEX IF NOT EXISTS idx_payment_invoice ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payment_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payment_date ON payments(payment_date);

-- ============================================
-- INSURANCE
-- ============================================

-- Insurance carriers
CREATE TABLE IF NOT EXISTS insurance_carriers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(20),
    address TEXT,
    phone VARCHAR(20),
    edi_payer_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_insurance_carrier_code ON insurance_carriers(code);

-- Patient insurance
CREATE TABLE IF NOT EXISTS patient_insurances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    carrier_id UUID NOT NULL REFERENCES insurance_carriers(id),
    policy_number VARCHAR(100) NOT NULL,
    group_number VARCHAR(100),
    subscriber_name VARCHAR(200),
    subscriber_dob DATE,
    relationship_to_subscriber VARCHAR(50),
    priority INTEGER DEFAULT 1,
    effective_date DATE,
    expiration_date DATE,
    coverage_info JSONB,
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patient_insurance_patient ON patient_insurances(patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_insurance_carrier ON patient_insurances(carrier_id);
CREATE INDEX IF NOT EXISTS idx_patient_insurance_policy ON patient_insurances(policy_number);

-- Insurance claims
CREATE TABLE IF NOT EXISTS insurance_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    insurance_id UUID NOT NULL REFERENCES patient_insurances(id),
    claim_number VARCHAR(50),
    date_of_service DATE,
    procedures JSONB,
    total_amount DECIMAL(10, 2),
    submitted_amount DECIMAL(10, 2),
    allowed_amount DECIMAL(10, 2),
    paid_amount DECIMAL(10, 2),
    patient_responsibility DECIMAL(10, 2),
    status VARCHAR(30) DEFAULT 'draft', -- draft, submitted, accepted, rejected, paid, denied, appealed
    submitted_at TIMESTAMP,
    processed_at TIMESTAMP,
    denial_reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_insurance_claim_patient ON insurance_claims(patient_id);
CREATE INDEX IF NOT EXISTS idx_insurance_claim_status ON insurance_claims(status);
CREATE INDEX IF NOT EXISTS idx_insurance_claim_date ON insurance_claims(date_of_service);

-- Insurance pre-authorizations
CREATE TABLE IF NOT EXISTS insurance_pre_authorizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    insurance_id UUID NOT NULL REFERENCES patient_insurances(id),
    treatment_plan_id UUID REFERENCES treatment_plans(id),
    authorization_number VARCHAR(100),
    procedures JSONB,
    requested_amount DECIMAL(10, 2),
    approved_amount DECIMAL(10, 2),
    status VARCHAR(30) DEFAULT 'pending', -- pending, approved, rejected, expired
    submitted_at TIMESTAMP,
    response_at TIMESTAMP,
    valid_until DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pre_auth_patient ON insurance_pre_authorizations(patient_id);

-- Eligibility checks
CREATE TABLE IF NOT EXISTS eligibility_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    insurance_id UUID NOT NULL REFERENCES patient_insurances(id),
    status VARCHAR(30) DEFAULT 'pending', -- pending, active, inactive, error
    response_data JSONB,
    checked_at TIMESTAMP,
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_eligibility_patient ON eligibility_checks(patient_id);

-- Explanation of Benefits
CREATE TABLE IF NOT EXISTS explanation_of_benefits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES insurance_claims(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    insurance_id UUID NOT NULL REFERENCES patient_insurances(id),
    eob_data JSONB,
    total_billed DECIMAL(10, 2),
    total_allowed DECIMAL(10, 2),
    insurance_paid DECIMAL(10, 2),
    patient_paid DECIMAL(10, 2),
    adjustment DECIMAL(10, 2),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_eob_claim ON explanation_of_benefits(claim_id);
CREATE INDEX IF NOT EXISTS idx_eob_patient ON explanation_of_benefits(patient_id);

-- ============================================
-- IMAGING
-- ============================================

-- Patient images
CREATE TABLE IF NOT EXISTS patient_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES users(id),
    title VARCHAR(255),
    description TEXT,
    image_url TEXT NOT NULL,
    thumbnail_url TEXT,
    image_type VARCHAR(50), -- xray, photo, scan, pan, cbct, intraoral
    tooth_numbers VARCHAR(50),
    notes TEXT,
    capture_date DATE,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patient_image_patient ON patient_images(patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_image_type ON patient_images(image_type);
CREATE INDEX IF NOT EXISTS idx_patient_image_capture ON patient_images(capture_date);

-- Image series
CREATE TABLE IF NOT EXISTS image_series (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    series_type VARCHAR(50), -- fm, bw, pan, ceph
    series_data JSONB,
    capture_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_image_series_patient ON image_series(patient_id);

-- Image templates
CREATE TABLE IF NOT EXISTS image_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50),
    template_data JSONB,
    practice_id UUID REFERENCES practices(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- BOOKING (Online appointments)
-- ============================================

-- Booking pages
CREATE TABLE IF NOT EXISTS booking_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_id UUID NOT NULL REFERENCES practices(id),
    slug VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_booking_page_slug ON booking_pages(slug);
CREATE INDEX IF NOT EXISTS idx_booking_page_practice ON booking_pages(practice_id);

-- Online bookings
CREATE TABLE IF NOT EXISTS online_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    provider_id UUID REFERENCES users(id),
    booking_page_id UUID REFERENCES booking_pages(id),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(30) DEFAULT 'pending', -- pending, confirmed, cancelled, no_show, completed
    notes TEXT,
    reminder_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_online_booking_status ON online_bookings(status);
CREATE INDEX IF NOT EXISTS idx_online_booking_start ON online_bookings(start_time);

-- Booking availability
CREATE TABLE IF NOT EXISTS booking_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_page_id UUID NOT NULL REFERENCES booking_pages(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES users(id),
    day_of_week INTEGER NOT NULL, -- 0=Sunday, 6=Saturday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    slot_duration INTEGER NOT NULL DEFAULT 30,
    max_bookings INTEGER DEFAULT 999,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_booking_availability_page ON booking_availability(booking_page_id);

-- Waitlist entries
CREATE TABLE IF NOT EXISTS waitlist_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES users(id),
    preferred_start DATE,
    preferred_end DATE,
    preferred_times JSONB,
    status VARCHAR(30) DEFAULT 'waiting', -- waiting, notified, booked, cancelled, expired
    notified_at TIMESTAMP,
    notified_slot TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_waitlist_patient ON waitlist_entries(patient_id);
CREATE INDEX IF NOT EXISTS idx_waitlist_status ON waitlist_entries(status);

-- Booking notifications
CREATE TABLE IF NOT EXISTS booking_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES online_bookings(id) ON DELETE CASCADE,
    recipient_email VARCHAR(255),
    recipient_phone VARCHAR(20),
    notification_type VARCHAR(30), -- confirmation, reminder, cancellation, reschedule
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) DEFAULT 'pending', -- pending, sent, failed
    response_data JSONB
);

CREATE INDEX IF NOT EXISTS idx_booking_notification_booking ON booking_notifications(booking_id);

-- ============================================
-- INVENTORY
-- ============================================

-- Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    website TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory categories
CREATE TABLE IF NOT EXISTS inventory_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    practice_id UUID REFERENCES practices(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory units
CREATE TABLE IF NOT EXISTS inventory_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    abbreviation VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory items
CREATE TABLE IF NOT EXISTS inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_id UUID NOT NULL REFERENCES practices(id),
    category_id UUID REFERENCES inventory_categories(id),
    supplier_id UUID REFERENCES suppliers(id),
    unit_id UUID REFERENCES inventory_units(id),
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100),
    description TEXT,
    current_stock DECIMAL(10, 2) DEFAULT 0,
    min_stock DECIMAL(10, 2) DEFAULT 0,
    max_stock DECIMAL(10, 2),
    unit_cost DECIMAL(10, 2),
    reorder_point DECIMAL(10, 2),
    location VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_practice ON inventory_items(practice_id);
CREATE INDEX IF NOT EXISTS idx_inventory_stock ON inventory_items(current_stock, min_stock);

-- Inventory transactions
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    transaction_type VARCHAR(30) NOT NULL, -- received, used, returned, adjusted, discarded
    quantity DECIMAL(10, 2) NOT NULL,
    previous_stock DECIMAL(10, 2),
    new_stock DECIMAL(10, 2),
    user_id UUID REFERENCES users(id),
    purchase_order_id UUID REFERENCES purchase_orders(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_transaction_item ON inventory_transactions(item_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transaction_type ON inventory_transactions(transaction_type);

-- Purchase orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_id UUID NOT NULL REFERENCES practices(id),
    supplier_id UUID NOT NULL REFERENCES suppliers(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(30) DEFAULT 'draft', -- draft, ordered, received, cancelled
    total_cost DECIMAL(10, 2),
    order_date DATE,
    expected_delivery_date DATE,
    received_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_purchase_order_practice ON purchase_orders(practice_id);

-- Purchase order items
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    quantity DECIMAL(10, 2) NOT NULL,
    unit_cost DECIMAL(10, 2),
    total_cost DECIMAL(10, 2),
    received_quantity DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory alerts
CREATE TABLE IF NOT EXISTS inventory_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL, -- low_stock, expired, reorder_due
    message TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_alert_item ON inventory_alerts(item_id);
CREATE INDEX IF NOT EXISTS idx_inventory_alert_resolved ON inventory_alerts(is_resolved);

-- ============================================
-- LAB MANAGEMENT
-- ============================================

-- Labs
CREATE TABLE IF NOT EXISTS labs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    website TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lab cases
CREATE TABLE IF NOT EXISTS lab_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    provider_id UUID NOT NULL REFERENCES users(id),
    lab_id UUID NOT NULL REFERENCES labs(id),
    case_number VARCHAR(50),
    case_type VARCHAR(100), -- crown, bridge, denture, implant, ortho, other
    description TEXT,
    instructions TEXT,
    shade VARCHAR(50),
    material VARCHAR(100),
    status VARCHAR(30) DEFAULT 'pending', -- pending, in_progress, completed, delivered, rejected
    sent_to_lab_date DATE,
    expected_delivery_date DATE,
    delivered_date DATE,
    cost DECIMAL(10, 2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lab_case_patient ON lab_cases(patient_id);
CREATE INDEX IF NOT EXISTS idx_lab_case_status ON lab_cases(status);
CREATE INDEX IF NOT EXISTS idx_lab_case_provider ON lab_cases(provider_id);

-- Lab invoices
CREATE TABLE IF NOT EXISTS lab_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lab_case_id UUID REFERENCES lab_cases(id) ON DELETE CASCADE,
    lab_id UUID NOT NULL REFERENCES labs(id),
    invoice_number VARCHAR(50),
    amount DECIMAL(10, 2),
    status VARCHAR(30) DEFAULT 'pending', -- pending, paid, disputed
    invoice_date DATE,
    paid_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lab_invoice_case ON lab_invoices(lab_case_id);

-- Lab communications
CREATE TABLE IF NOT EXISTS lab_communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lab_case_id UUID NOT NULL REFERENCES lab_cases(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id),
    message TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lab_communication_case ON lab_communications(lab_case_id);

-- ============================================
-- REFERRALS
-- ============================================

-- Referral sources
CREATE TABLE IF NOT EXISTS referral_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- dentist, doctor, patient, ad, website, other
    contact_name VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_referral_source_type ON referral_sources(type);

-- Referrals
CREATE TABLE IF NOT EXISTS referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    source_id UUID REFERENCES referral_sources(id),
    referred_by_id UUID REFERENCES users(id),
    referred_to_id UUID REFERENCES users(id),
    reason TEXT,
    notes TEXT,
    status VARCHAR(30) DEFAULT 'pending', -- pending, accepted, completed, declined
    referral_date DATE,
    response_date DATE,
    outcome TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_referral_patient ON referrals(patient_id);
CREATE INDEX IF NOT EXISTS idx_referral_status ON referrals(status);

-- Referral communications
CREATE TABLE IF NOT EXISTS referral_communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_id UUID NOT NULL REFERENCES referrals(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id),
    message TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_referral_comm_referral ON referral_communications(referral_id);

-- Referral reports
CREATE TABLE IF NOT EXISTS referral_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_id UUID NOT NULL REFERENCES referrals(id) ON DELETE CASCADE,
    report_data JSONB,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_referral_report ON referral_reports(referral_id);

-- ============================================
-- COMMUNICATIONS
-- ============================================

-- Message templates
CREATE TABLE IF NOT EXISTS message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    body TEXT,
    channel VARCHAR(30), -- email, sms, internal
    category VARCHAR(100),
    practice_id UUID REFERENCES practices(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patient messages
CREATE TABLE IF NOT EXISTS patient_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    template_id UUID REFERENCES message_templates(id),
    channel VARCHAR(30) NOT NULL, -- email, sms
    subject VARCHAR(500),
    body TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'pending', -- pending, sent, delivered, failed
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patient_message_patient ON patient_messages(patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_message_status ON patient_messages(status);

-- Reminder schedules
CREATE TABLE IF NOT EXISTS reminder_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    reminder_type VARCHAR(50), -- appointment, recall, birthday, followup
    channel VARCHAR(30), -- email, sms, both
    timing_days INTEGER[], -- days before event
    template_id UUID REFERENCES message_templates(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    subject VARCHAR(500),
    status VARCHAR(30) DEFAULT 'open', -- open, closed, archived
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversation_patient ON conversations(patient_id);
CREATE INDEX IF NOT EXISTS idx_conversation_status ON conversations(status);

-- Conversation messages
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(id),
    message_type VARCHAR(30) DEFAULT 'text', -- text, attachment, system
    content TEXT,
    attachments JSONB DEFAULT '[]',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversation_msg ON conversation_messages(conversation_id);

-- ============================================
-- DOCUMENTS
-- ============================================

-- Document templates
CREATE TABLE IF NOT EXISTS document_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    template_data JSONB,
    practice_id UUID REFERENCES practices(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    template_id UUID REFERENCES document_templates(id),
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(100),
    file_url TEXT,
    status VARCHAR(30) DEFAULT 'draft', -- draft, pending_signature, signed, archived
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_document_patient ON documents(patient_id);
CREATE INDEX IF NOT EXISTS idx_document_status ON documents(status);

-- Document signatures
CREATE TABLE IF NOT EXISTS document_signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    signer_name VARCHAR(255) NOT NULL,
    signer_email VARCHAR(255),
    relationship VARCHAR(100),
    signature_data JSONB,
    signed_at TIMESTAMP,
    ip_address VARCHAR(45),
    status VARCHAR(30) DEFAULT 'pending', -- pending, signed, declined
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_document_sig_document ON document_signatures(document_id);

-- ============================================
-- MARKETING
-- ============================================

-- Marketing templates
CREATE TABLE IF NOT EXISTS marketing_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    body TEXT,
    template_type VARCHAR(50), -- email, sms, social
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaigns
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    template_id UUID REFERENCES marketing_templates(id),
    status VARCHAR(30) DEFAULT 'draft', -- draft, scheduled, running, paused, completed
    campaign_type VARCHAR(50),
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    total_recipients INTEGER DEFAULT 0,
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    bounced_count INTEGER DEFAULT 0,
    unsubscribed_count INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_campaign_status ON campaigns(status);

-- Campaign segments
CREATE TABLE IF NOT EXISTS campaign_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    segment_criteria JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_campaign_segment ON campaign_segments(campaign_id);

-- Marketing emails
CREATE TABLE IF NOT EXISTS marketing_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(200),
    status VARCHAR(30) DEFAULT 'pending', -- pending, sent, delivered, opened, clicked, bounced, unsubscribed
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_marketing_email_campaign ON marketing_emails(campaign_id);
CREATE INDEX IF NOT EXISTS idx_marketing_email_status ON marketing_emails(status);

-- Newsletter subscriptions
CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(200),
    patient_id UUID REFERENCES patients(id),
    is_subscribed BOOLEAN DEFAULT TRUE,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unsubscribed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_newsletter_email ON newsletter_subscriptions(email);

-- ============================================
-- PAYMENT PROCESSING
-- ============================================

-- Payment cards
CREATE TABLE IF NOT EXISTS payment_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    card_type VARCHAR(50), -- visa, mastercard, amex, discover
    last_four VARCHAR(4),
    exp_month VARCHAR(2),
    exp_year VARCHAR(4),
    cardholder_name VARCHAR(255),
    stripe_payment_method_id VARCHAR(255),
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_card_patient ON payment_cards(patient_id);

-- Payment transactions
CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    stripe_charge_id VARCHAR(255),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(30) DEFAULT 'pending', -- pending, processing, completed, failed, refunded
    error_message TEXT,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_transaction ON payment_transactions(payment_id);
CREATE INDEX IF NOT EXISTS idx_payment_transaction_stripe ON payment_transactions(stripe_charge_id);

-- Recurring billing
CREATE TABLE IF NOT EXISTS recurring_billing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    card_id UUID REFERENCES payment_cards(id),
    amount DECIMAL(10, 2) NOT NULL,
    frequency VARCHAR(30), -- monthly, quarterly, annually
    start_date DATE,
    end_date DATE,
    next_billing_date DATE,
    status VARCHAR(30) DEFAULT 'active', -- active, paused, cancelled, expired
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recurring_billing_patient ON recurring_billing(patient_id);
CREATE INDEX IF NOT EXISTS idx_recurring_billing_status ON recurring_billing(status);

-- Payment terminals
CREATE TABLE IF NOT EXISTS payment_terminals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_id UUID NOT NULL REFERENCES practices(id),
    terminal_id VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment settings
CREATE TABLE IF NOT EXISTS payment_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_id UUID NOT NULL REFERENCES practices(id) UNIQUE,
    stripe_connect_id VARCHAR(255),
    stripe_publishable_key VARCHAR(255),
    accept_credit BOOLEAN DEFAULT TRUE,
    accept_debit BOOLEAN DEFAULT TRUE,
    accept_checks BOOLEAN DEFAULT FALSE,
    processing_fee_percentage DECIMAL(5, 2) DEFAULT 2.9,
    processing_fee_fixed DECIMAL(5, 2) DEFAULT 0.30,
    auto_charge BOOLEAN DEFAULT FALSE,
    late_fee_percentage DECIMAL(5, 2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Enum types (PostgreSQL specific)
-- ============================================

-- Create enum types if they don't exist
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('owner', 'admin', 'dentist', 'hygienist', 'front_desk', 'group_owner', 'group_admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE patient_status AS ENUM ('active', 'inactive');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE gender AS ENUM ('male', 'female', 'other');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;