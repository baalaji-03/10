-- Seed Data for Pharmacy Management System
USE pharmacy_db;

-- Insert Roles
INSERT INTO roles (id, name, description) VALUES
(1, 'Admin', 'Full administrative access across all modules, settings, reports, and user management'),
(2, 'Pharmacist', 'Access to billing, medicine registry, inventory, batches, expiry alerts, and purchases'),
(3, 'Cashier', 'Dedicated fast POS billing, customer search/add, and receipt reprint access'),
(4, 'Inventory Staff', 'Stock entry, purchase management, supplier tracking, and stock movement auditing')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- Default Pharmacy Settings
INSERT INTO pharmacy_settings (
    id, pharmacy_name, tagline, address_line1, address_line2, city, state, postal_code,
    phone, email, gstin, dl_number, pan_number, state_code, invoice_prefix,
    invoice_declaration, currency_symbol, expiry_warning_months, default_reorder_multiplier
) VALUES (
    1,
    'Baalaji Medicals & Healthcare',
    'Your Trusted 24x7 Neighborhood Pharmacy',
    'No. 45, G.S.T. Road, Tambaram Sanatorium',
    'Opposite Government Hospital',
    'Chennai',
    'Tamil Nadu',
    '600047',
    '+91 94440 12345',
    'care@baalajimedicals.com',
    '33AAAAA9876B1Z8',
    'TN-CHE-20B-78901, TN-CHE-21B-78902',
    'AAAAA9876B',
    '33',
    'BM',
    '1. Goods once sold will not be taken back without original bill.\n2. Prescribed medicines will not be dispensed without a valid registered doctor prescription.\n3. Storage instructions: Store below 25°C in a dry place.',
    '₹',
    6,
    2.00
) ON DUPLICATE KEY UPDATE pharmacy_name=VALUES(pharmacy_name);

-- Default Admin User (Password: Admin@123)
INSERT INTO users (id, username, email, full_name, password_hash, role, role_id, is_active) VALUES
(1, 'admin', 'admin@baalajimedicals.com', 'System Administrator', '$2b$12$5dV8GDsHsGjexf2fPwwLWuP/RPLx5iIvasA44fN3d/KA1e.nD2gOG', 'Admin', 1, TRUE),
(2, 'pharmacist', 'pharma@baalajimedicals.com', 'K. Baalaji, B.Pharm', '$2b$12$5dV8GDsHsGjexf2fPwwLWuP/RPLx5iIvasA44fN3d/KA1e.nD2gOG', 'Pharmacist', 2, TRUE),
(3, 'cashier', 'billing@baalajimedicals.com', 'M. Saravanan', '$2b$12$5dV8GDsHsGjexf2fPwwLWuP/RPLx5iIvasA44fN3d/KA1e.nD2gOG', 'Cashier', 3, TRUE),
(4, 'inventory', 'store@baalajimedicals.com', 'R. Suresh', '$2b$12$5dV8GDsHsGjexf2fPwwLWuP/RPLx5iIvasA44fN3d/KA1e.nD2gOG', 'Inventory Staff', 4, TRUE)
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);

-- Sample Suppliers
INSERT INTO suppliers (id, supplier_code, name, contact_person, phone, email, gstin, address, city, state, dl_number, outstanding_balance) VALUES
(1, 'SUP-001', 'Apollo Med Wholesale Ltd', 'Ramanathan', '+91 98401 22334', 'orders@apollomedwholesale.com', '33AAACA1234D1Z1', '44 Industrial Estate, Guindy', 'Chennai', 'Tamil Nadu', 'TN-CHE-20B-33445', 12500.00),
(2, 'SUP-002', 'Sun Pharma Distribution Hub', 'Venkatesh S', '+91 97910 88990', 'southhub@sunpharma.com', '33AABCS5678E1Z9', '12 Ring Road Logistics Park', 'Chennai', 'Tamil Nadu', 'TN-CHE-21B-99887', 0.00),
(3, 'SUP-003', 'Cipla Care Agencies', 'Meenakshi Sundaram', '+91 94432 11002', 'chennaidist@ciplacare.com', '33AACCC9012F1Z4', '77 Mount Road, Teynampet', 'Chennai', 'Tamil Nadu', 'TN-CHE-20B-66554', 4500.00)
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- Sample Customers
INSERT INTO customers (id, customer_code, name, mobile, email, address, gender) VALUES
(1, 'CUST-0001', 'Dr. Rajesh Kumar', '9840011223', 'dr.rajesh@gmail.com', '12/4 2nd Avenue, Anna Nagar East, Chennai', 'Male'),
(2, 'CUST-0002', 'Lakshmi Narayanan', '9841234567', 'lakshmi.n@yahoo.com', '45 North Usman Road, T. Nagar, Chennai', 'Female'),
(3, 'CUST-0003', 'Anand Swaminathan', '9790987654', 'anand.swamy@gmail.com', '88 Velachery Main Road, Chennai', 'Male')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- Sample Medicines
INSERT INTO medicines (id, item_code, barcode, name, generic_name, manufacturer, category, hsn_code, gst_rate, rack_location, unit, min_stock_level, default_purchase_price, default_selling_price, is_prescription_required) VALUES
(1, 'MED-0001', '8901088001122', 'Dolo 650mg Tablet', 'Paracetamol 650mg', 'Micro Labs Ltd', 'Analgesic / Antipyretic', '3004', 12.00, 'Rack-A1', 'Strip (15 Tab)', 20, 24.50, 33.60, FALSE),
(2, 'MED-0002', '8901148002233', 'Augmentin 625 Duo', 'Amoxicillin + Clavulanic Acid 625mg', 'GlaxoSmithKline', 'Antibiotic', '3004', 12.00, 'Rack-B3', 'Strip (10 Tab)', 15, 145.00, 201.50, TRUE),
(3, 'MED-0003', '8901234003344', 'Pan 40 Tablet', 'Pantoprazole 40mg', 'Alkem Laboratories', 'Gastrointestinal', '3004', 12.00, 'Rack-A3', 'Strip (15 Tab)', 25, 95.00, 155.00, FALSE),
(4, 'MED-0004', '8901345004455', 'Azithral 500mg', 'Azithromycin 500mg', 'Alembic Pharma', 'Antibiotic', '3004', 12.00, 'Rack-B1', 'Strip (5 Tab)', 10, 82.00, 119.50, TRUE),
(5, 'MED-0005', '8901456005566', 'Glycomet GP 1', 'Glimepiride 1mg + Metformin 500mg', 'USV Private Ltd', 'Antidiabetic', '3004', 12.00, 'Rack-C2', 'Strip (15 Tab)', 30, 85.00, 128.00, TRUE),
(6, 'MED-0006', '8901567006677', 'Telma 40 Tablet', 'Telmisartan 40mg', 'Glenmark Pharma', 'Cardiovascular', '3004', 12.00, 'Rack-C4', 'Strip (30 Tab)', 15, 180.00, 260.00, TRUE),
(7, 'MED-0007', '8901678007788', 'Montair LC Tablet', 'Levocetirizine + Montelukast', 'Cipla Ltd', 'Respiratory / Antiallergic', '3004', 12.00, 'Rack-D1', 'Strip (10 Tab)', 20, 130.00, 198.00, FALSE),
(8, 'MED-0008', '8901789008899', 'Becosules Z Capsules', 'Vitamin B-Complex with Zinc', 'Pfizer India', 'Vitamins & Supplements', '3004', 12.00, 'Rack-E2', 'Strip (20 Cap)', 25, 32.00, 48.00, FALSE),
(9, 'MED-0009', '8901890009900', 'Shelcal 500 Tablet', 'Calcium 500mg + Vitamin D3', 'Torrent Pharma', 'Minerals & Supplements', '3004', 12.00, 'Rack-E4', 'Strip (15 Tab)', 15, 88.00, 131.00, FALSE),
(10, 'MED-0010', '8901901010011', 'Vicks Vaporub 25g', 'Menthol, Camphor, Eucalyptus', 'Procter & Gamble', 'OTC Balms', '3004', 18.00, 'Front Counter', 'Jar', 10, 68.00, 95.00, FALSE)
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- Sample Batches (including Available, Low Stock, Near-Expiry, and Expired for testing)
INSERT INTO medicine_batches (id, medicine_id, batch_number, manufacturing_date, expiry_date, purchase_price, mrp, selling_price, quantity, supplier_id, status) VALUES
-- Dolo 650: Normal stock
(1, 1, 'DL2026A', '2026-01-10', '2028-06-30', 24.50, 33.60, 33.60, 120, 1, 'AVAILABLE'),
-- Augmentin: Low stock alert
(2, 2, 'AG9901B', '2026-02-15', '2027-12-31', 145.00, 201.50, 201.50, 4, 2, 'LOW_STOCK'),
-- Pan 40: Normal stock
(3, 3, 'PAN8811', '2026-03-01', '2028-02-28', 95.00, 155.00, 155.00, 80, 1, 'AVAILABLE'),
-- Azithral: Expiring in 2 months (Near Expiry - Orange Alert)
(4, 4, 'AZ6060X', '2025-01-01', '2026-12-15', 82.00, 119.50, 119.50, 18, 3, 'AVAILABLE'),
-- Glycomet GP1: Expiring in 4 months (Near Expiry - Orange Alert)
(5, 5, 'GLY4420', '2025-03-10', '2027-02-20', 85.00, 128.00, 128.00, 22, 1, 'AVAILABLE'),
-- Telma 40: Normal stock
(6, 6, 'TEL3030', '2026-04-10', '2028-09-30', 180.00, 260.00, 260.00, 50, 2, 'AVAILABLE'),
-- Montair LC: Already Expired (Red Alert - MUST NOT BE SOLD)
(7, 7, 'MNT1009', '2024-05-01', '2026-08-31', 130.00, 198.00, 198.00, 15, 3, 'EXPIRED'),
-- Becosules Z: Normal stock
(8, 8, 'BEC7788', '2026-05-15', '2028-04-30', 32.00, 48.00, 48.00, 95, 1, 'AVAILABLE'),
-- Shelcal 500: Normal stock
(9, 9, 'SHL5544', '2026-06-01', '2028-05-31', 88.00, 131.00, 131.00, 60, 2, 'AVAILABLE'),
-- Vicks: Normal stock
(10, 10, 'VK0909A', '2026-01-20', '2029-01-19', 68.00, 95.00, 95.00, 35, 1, 'AVAILABLE')
ON DUPLICATE KEY UPDATE batch_number=VALUES(batch_number);

-- Initial Stock Movement Log for initial batch setup
INSERT INTO stock_movements (medicine_id, batch_id, movement_type, quantity_changed, previous_quantity, new_quantity, reference_type, notes) VALUES
(1, 1, 'PURCHASE', 120, 0, 120, 'INITIAL_SETUP', 'Initial inventory opening stock'),
(2, 2, 'PURCHASE', 4, 0, 4, 'INITIAL_SETUP', 'Initial inventory opening stock (Low Stock)'),
(3, 3, 'PURCHASE', 80, 0, 80, 'INITIAL_SETUP', 'Initial inventory opening stock'),
(4, 4, 'PURCHASE', 18, 0, 18, 'INITIAL_SETUP', 'Initial inventory opening stock (Near Expiry)'),
(5, 5, 'PURCHASE', 22, 0, 22, 'INITIAL_SETUP', 'Initial inventory opening stock (Near Expiry)'),
(6, 6, 'PURCHASE', 50, 0, 50, 'INITIAL_SETUP', 'Initial inventory opening stock'),
(7, 7, 'PURCHASE', 15, 0, 15, 'INITIAL_SETUP', 'Opening stock - expired batch for testing quarantine'),
(8, 8, 'PURCHASE', 95, 0, 95, 'INITIAL_SETUP', 'Initial inventory opening stock'),
(9, 9, 'PURCHASE', 60, 0, 60, 'INITIAL_SETUP', 'Initial inventory opening stock'),
(10, 10, 'PURCHASE', 35, 0, 35, 'INITIAL_SETUP', 'Initial inventory opening stock');
