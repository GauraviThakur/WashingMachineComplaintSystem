
-- ============================================================
-- Washing Machine Complaint Management System
-- File: sql/10_seed_manufacturing_data.sql
-- Purpose: Add 200 synthetic manufacturing records
-- Existing records are preserved.
-- ============================================================

BEGIN;

INSERT INTO machines (
    serial_number,
    model_number,
    batch_number,
    manufacturing_date
)
SELECT
    'WM-2026-' || LPAD(machine_number::TEXT, 4, '0'),
    CASE
        WHEN machine_number % 3 = 1 THEN 'WM-Pro-100'
        WHEN machine_number % 3 = 2 THEN 'WM-Eco-200'
        ELSE 'WM-Premium-300'
    END,
    'BATCH-2026-' || LPAD(
        (((machine_number - 1) / 20) + 1)::TEXT,
        2,
        '0'
    ),
    DATE '2026-01-01' + (machine_number * 2)
FROM generate_series(6, 205) AS machine_number
ON CONFLICT (serial_number) DO NOTHING;

COMMIT;
