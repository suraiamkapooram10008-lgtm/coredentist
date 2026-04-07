-- GST Fields Migration for Railway/Supabase
-- Run this SQL directly on your PostgreSQL database

-- GST Identification Number (15 characters: 2 state code + 10 PAN + 1 entity number + 1 Z + 1 default checksum)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS gstin VARCHAR(15);

-- GST Rate (default 18% for most dental services)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS gst_rate NUMERIC(5,2) DEFAULT 18.00 NOT NULL;

-- Central GST amount (half of total GST for intra-state supplies)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS cgst_amount NUMERIC(10,2) DEFAULT 0 NOT NULL;

-- State GST amount (half of total GST for intra-state supplies)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS sgst_amount NUMERIC(10,2) DEFAULT 0 NOT NULL;

-- Integrated GST amount (full GST for inter-state supplies)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS igst_amount NUMERIC(10,2) DEFAULT 0 NOT NULL;

-- Inter-state flag (Y/N)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS is_inter_state VARCHAR(1) DEFAULT 'N' NOT NULL;

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_invoices_gstin ON invoices(gstin);
CREATE INDEX IF NOT EXISTS idx_invoices_is_inter_state ON invoices(is_inter_state);

-- Comment for documentation
COMMENT ON COLUMN invoices.gstin IS 'GST Identification Number (Indian tax compliance)';
COMMENT ON COLUMN invoices.gst_rate IS 'GST rate percentage (default 18%)';
COMMENT ON COLUMN invoices.cgst_amount IS 'Central GST amount (intra-state)';
COMMENT ON COLUMN invoices.sgst_amount IS 'State GST amount (intra-state)';
COMMENT ON COLUMN invoices.igst_amount IS 'Integrated GST amount (inter-state)';
COMMENT ON COLUMN invoices.is_inter_state IS 'Inter-state supply flag (Y/N)';