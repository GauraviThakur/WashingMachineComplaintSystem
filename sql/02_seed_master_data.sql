
-- ============================================================
-- Washing Machine Complaint Management System
-- File: sql/02_seed_master_data.sql
-- Purpose: Insert initial master data for development/testing
-- ============================================================

BEGIN;

-- Complaint categories
INSERT INTO complaint_categories (category_name, description)
VALUES
    ('Electrical', 'Electrical and power-related issues'),
    ('Mechanical', 'Mechanical and moving-part issues'),
    ('Water Leakage', 'Water leakage and sealing issues'),
    ('Performance', 'Washing and operating performance issues'),
    ('Installation', 'Installation-related issues')
ON CONFLICT (category_name) DO NOTHING;

-- Issue types
INSERT INTO issue_types (category_id, issue_type_name, description)
SELECT c.category_id, seed.issue_type_name, seed.description
FROM (
    VALUES
        ('Electrical', 'Machine Not Starting',
         'Machine does not power on or start'),
        ('Electrical', 'Power Failure',
         'Machine experiences power interruption'),
        ('Electrical', 'Control Panel Failure',
         'Buttons, display, or control panel malfunction'),
        ('Electrical', 'Voltage Abnormality',
         'Electrical voltage-related abnormal behaviour'),
        ('Mechanical', 'Abnormal Noise',
         'Unusual noise during machine operation'),
        ('Mechanical', 'Excessive Vibration',
         'Machine vibrates excessively during operation'),
        ('Mechanical', 'Drum Not Rotating',
         'Drum fails to rotate correctly'),
        ('Water Leakage', 'Water Leakage',
         'Water leaks from the machine'),
        ('Water Leakage', 'Drainage Problem',
         'Machine fails to drain water properly'),
        ('Performance', 'Poor Washing Performance',
         'Clothes are not being washed effectively'),
        ('Performance', 'Water Not Filling',
         'Machine does not fill with water correctly'),
        ('Performance', 'Water Not Heating',
         'Water heating function does not work correctly'),
        ('Installation', 'Installation Defect',
         'Issue related to machine installation')
) AS seed(category_name, issue_type_name, description)
JOIN complaint_categories c
    ON c.category_name = seed.category_name
ON CONFLICT (issue_type_name) DO NOTHING;

-- Sample machines for development and API testing
INSERT INTO machines (
    serial_number,
    model_number,
    batch_number,
    manufacturing_date
)
VALUES
    ('WM-2026-0001', 'WM-Pro-100', 'BATCH-2026-01', DATE '2026-01-10'),
    ('WM-2026-0002', 'WM-Pro-100', 'BATCH-2026-01', DATE '2026-01-12'),
    ('WM-2026-0003', 'WM-Eco-200', 'BATCH-2026-02', DATE '2026-02-05'),
    ('WM-2026-0004', 'WM-Eco-200', 'BATCH-2026-02', DATE '2026-02-08'),
    ('WM-2026-0005', 'WM-Premium-300', 'BATCH-2026-03', DATE '2026-03-15')
ON CONFLICT (serial_number) DO NOTHING;

COMMIT;
