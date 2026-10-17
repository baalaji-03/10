-- Pharmacy Management System - MySQL 8.0+ Database Schema
-- Charset: utf8mb4, Engine: InnoDB

CREATE DATABASE IF NOT EXISTS pharmacy_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pharmacy_db;

-- 1. Roles and Permissions
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    description VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 2. Users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Pharmacist',
    role_id INT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL,
    INDEX idx_user_role (role)
) ENGINE=InnoDB;

-- 3. Pharmacy Settings
CREATE TABLE IF NOT EXISTS pharmacy_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pharmacy_name VARCHAR(150) NOT NULL DEFAULT 'Baalaji Medicals & Pharmacy',
    tagline VARCHAR(200) DEFAULT 'Care, Trust & Wellness',
    address_line1 VARCHAR(255) DEFAULT '123 Cross Road, Anna Nagar',
    address_line2 VARCHAR(255) DEFAULT 'Main Commercial Complex',
    city VARCHAR(100) DEFAULT 'Chennai',
    state VARCHAR(100) DEFAULT 'Tamil Nadu',
    postal_code VARCHAR(20) DEFAULT '600040',
    phone VARCHAR(30) DEFAULT '+91 98765 43210',
    email VARCHAR(100) DEFAULT 'info@baalajipharmacy.com',
    gstin VARCHAR(30) DEFAULT '33AAAAA0000A1Z5',
    dl_number VARCHAR(100) DEFAULT 'DL-TN-20B-12345, 21B-12346',
    pan_number VARCHAR(30) DEFAULT 'AAAAA0000A',
    state_code VARCHAR(10) DEFAULT '33',
    invoice_prefix VARCHAR(10) DEFAULT 'INV',
    invoice_declaration TEXT,
    currency_symbol VARCHAR(10) DEFAULT '₹',
    smtp_host VARCHAR(150) DEFAULT '',
    smtp_port INT DEFAULT 587,
    smtp_user VARCHAR(100) DEFAULT '',
    smtp_password VARCHAR(255) DEFAULT '',
    smtp_use_tls BOOLEAN DEFAULT TRUE,
    smtp_from_email VARCHAR(100) DEFAULT '',
    alert_email_recipient VARCHAR(200) DEFAULT '',
    expiry_warning_months INT DEFAULT 6,
    default_reorder_multiplier DECIMAL(5,2) DEFAULT 2.00,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. Customers
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_code VARCHAR(30) UNIQUE,
    name VARCHAR(100) NOT NULL,
    mobile VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100),
    address TEXT,
    date_of_birth DATE NULL,
    gender VARCHAR(10) DEFAULT 'Other',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer_mobile (mobile),
    INDEX idx_customer_name (name)
) ENGINE=InnoDB;

-- 5. Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_code VARCHAR(30) UNIQUE,
    name VARCHAR(150) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(100),
    gstin VARCHAR(30),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    state_code VARCHAR(10) DEFAULT '33',
    dl_number VARCHAR(100),
    pan_number VARCHAR(30),
    outstanding_balance DECIMAL(12,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_supplier_name (name),
    INDEX idx_supplier_gstin (gstin)
) ENGINE=InnoDB;

-- 6. Medicines (Master Catalog)
CREATE TABLE IF NOT EXISTS medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_code VARCHAR(50) UNIQUE,
    barcode VARCHAR(100) UNIQUE,
    name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),
    manufacturer VARCHAR(150),
    category VARCHAR(100) DEFAULT 'Allopathy',
    hsn_code VARCHAR(20) DEFAULT '3004',
    gst_rate DECIMAL(5,2) DEFAULT 12.00,
    rack_location VARCHAR(50),
    unit VARCHAR(20) DEFAULT 'Strip',
    min_stock_level INT DEFAULT 10,
    default_purchase_price DECIMAL(10,2) DEFAULT 0.00,
    default_selling_price DECIMAL(10,2) DEFAULT 0.00,
    is_prescription_required BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_med_name (name),
    INDEX idx_med_barcode (barcode),
    INDEX idx_med_generic (generic_name),
    INDEX idx_med_hsn (hsn_code)
) ENGINE=InnoDB;

-- 7. Medicine Batches (Track every batch separately)
CREATE TABLE IF NOT EXISTS medicine_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    batch_number VARCHAR(100) NOT NULL,
    manufacturing_date DATE NULL,
    expiry_date DATE NOT NULL,
    purchase_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    mrp DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    selling_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    quantity INT NOT NULL DEFAULT 0,
    free_quantity INT NOT NULL DEFAULT 0,
    supplier_id INT NULL,
    status ENUM('AVAILABLE', 'LOW_STOCK', 'EXPIRED', 'QUARANTINED', 'DEPLETED') DEFAULT 'AVAILABLE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE RESTRICT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
    UNIQUE KEY uk_medicine_batch (medicine_id, batch_number),
    INDEX idx_batch_expiry (expiry_date),
    INDEX idx_batch_num (batch_number),
    INDEX idx_batch_qty (quantity)
) ENGINE=InnoDB;

-- 8. Purchases (Purchase Invoices from Suppliers)
CREATE TABLE IF NOT EXISTS purchases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_number VARCHAR(50) NOT NULL UNIQUE,
    supplier_id INT NOT NULL,
    supplier_invoice_number VARCHAR(100) NOT NULL,
    invoice_date DATE NOT NULL,
    received_date DATE NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    discount_amount DECIMAL(12,2) DEFAULT 0.00,
    cgst_amount DECIMAL(12,2) DEFAULT 0.00,
    sgst_amount DECIMAL(12,2) DEFAULT 0.00,
    igst_amount DECIMAL(12,2) DEFAULT 0.00,
    tax_amount DECIMAL(12,2) DEFAULT 0.00,
    additional_charges DECIMAL(12,2) DEFAULT 0.00,
    round_off DECIMAL(6,2) DEFAULT 0.00,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    paid_amount DECIMAL(12,2) DEFAULT 0.00,
    balance_amount DECIMAL(12,2) DEFAULT 0.00,
    payment_status ENUM('PENDING', 'PARTIAL', 'PAID') DEFAULT 'PENDING',
    status ENUM('DRAFT', 'CONFIRMED', 'CANCELLED') DEFAULT 'CONFIRMED',
    notes TEXT,
    created_by_user_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY uk_supplier_invoice (supplier_id, supplier_invoice_number),
    INDEX idx_purchase_date (invoice_date)
) ENGINE=InnoDB;

-- 9. Purchase Items
CREATE TABLE IF NOT EXISTS purchase_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_id INT NOT NULL,
    medicine_id INT NOT NULL,
    batch_id INT NULL,
    batch_number VARCHAR(100) NOT NULL,
    manufacturing_date DATE NULL,
    expiry_date DATE NOT NULL,
    quantity INT NOT NULL,
    free_quantity INT DEFAULT 0,
    purchase_price DECIMAL(10,2) NOT NULL,
    mrp DECIMAL(10,2) NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0.00,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    gst_rate DECIMAL(5,2) NOT NULL DEFAULT 12.00,
    cgst_rate DECIMAL(5,2) DEFAULT 6.00,
    sgst_rate DECIMAL(5,2) DEFAULT 6.00,
    igst_rate DECIMAL(5,2) DEFAULT 0.00,
    cgst_amount DECIMAL(10,2) DEFAULT 0.00,
    sgst_amount DECIMAL(10,2) DEFAULT 0.00,
    igst_amount DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE RESTRICT,
    FOREIGN KEY (batch_id) REFERENCES medicine_batches(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 10. Supplier Payments
CREATE TABLE IF NOT EXISTS supplier_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    payment_number VARCHAR(50) NOT NULL UNIQUE,
    supplier_id INT NOT NULL,
    purchase_id INT NULL,
    payment_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    payment_method ENUM('CASH', 'UPI', 'BANK_TRANSFER', 'CHEQUE', 'CREDIT') DEFAULT 'BANK_TRANSFER',
    reference_number VARCHAR(100),
    notes TEXT,
    created_by_user_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE RESTRICT,
    FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 11. Sales (POS Invoices)
CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id INT NULL,
    customer_name VARCHAR(100) DEFAULT 'Walk-in Customer',
    customer_mobile VARCHAR(20),
    doctor_name VARCHAR(100),
    invoice_date DATE NOT NULL,
    invoice_time TIME NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    discount_amount DECIMAL(12,2) DEFAULT 0.00,
    taxable_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    cgst_amount DECIMAL(12,2) DEFAULT 0.00,
    sgst_amount DECIMAL(12,2) DEFAULT 0.00,
    igst_amount DECIMAL(12,2) DEFAULT 0.00,
    tax_amount DECIMAL(12,2) DEFAULT 0.00,
    round_off DECIMAL(6,2) DEFAULT 0.00,
    net_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    paid_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    balance_amount DECIMAL(12,2) DEFAULT 0.00,
    payment_method ENUM('CASH', 'UPI', 'CARD', 'CREDIT', 'MIXED') DEFAULT 'CASH',
    payment_status ENUM('PAID', 'PARTIAL', 'CREDIT') DEFAULT 'PAID',
    status ENUM('COMPLETED', 'CANCELLED', 'RETURNED') DEFAULT 'COMPLETED',
    total_cost_of_goods DECIMAL(12,2) DEFAULT 0.00,
    gross_profit DECIMAL(12,2) DEFAULT 0.00,
    user_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_sale_date (invoice_date),
    INDEX idx_sale_num (invoice_number),
    INDEX idx_sale_customer (customer_id)
) ENGINE=InnoDB;

-- 12. Sale Items
CREATE TABLE IF NOT EXISTS sale_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    medicine_id INT NOT NULL,
    batch_id INT NOT NULL,
    medicine_name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),
    batch_number VARCHAR(100) NOT NULL,
    expiry_date DATE NOT NULL,
    hsn_code VARCHAR(20) DEFAULT '3004',
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    purchase_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    mrp DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0.00,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    taxable_amount DECIMAL(10,2) NOT NULL,
    gst_rate DECIMAL(5,2) NOT NULL DEFAULT 12.00,
    cgst_rate DECIMAL(5,2) DEFAULT 6.00,
    sgst_rate DECIMAL(5,2) DEFAULT 6.00,
    igst_rate DECIMAL(5,2) DEFAULT 0.00,
    cgst_amount DECIMAL(10,2) DEFAULT 0.00,
    sgst_amount DECIMAL(10,2) DEFAULT 0.00,
    igst_amount DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(12,2) NOT NULL,
    cost_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    profit_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE RESTRICT,
    FOREIGN KEY (batch_id) REFERENCES medicine_batches(id) ON DELETE RESTRICT,
    INDEX idx_item_medicine (medicine_id),
    INDEX idx_item_batch (batch_id)
) ENGINE=InnoDB;

-- 13. Payments (Sales Payment Receipts)
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    payment_method ENUM('CASH', 'UPI', 'CARD', 'CREDIT') DEFAULT 'CASH',
    amount DECIMAL(12,2) NOT NULL,
    transaction_ref VARCHAR(100),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INT NULL,
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 14. Purchase Returns
CREATE TABLE IF NOT EXISTS purchase_returns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    return_number VARCHAR(50) NOT NULL UNIQUE,
    purchase_id INT NULL,
    supplier_id INT NOT NULL,
    return_date DATE NOT NULL,
    reason TEXT,
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    tax_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    total_refund_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    status ENUM('PENDING', 'APPROVED', 'COMPLETED') DEFAULT 'COMPLETED',
    created_by_user_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS purchase_return_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_return_id INT NOT NULL,
    medicine_id INT NOT NULL,
    batch_id INT NOT NULL,
    batch_number VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    unit_cost DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (purchase_return_id) REFERENCES purchase_returns(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE RESTRICT,
    FOREIGN KEY (batch_id) REFERENCES medicine_batches(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 15. Sales Returns
CREATE TABLE IF NOT EXISTS sales_returns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    return_number VARCHAR(50) NOT NULL UNIQUE,
    sale_id INT NOT NULL,
    customer_id INT NULL,
    return_date DATE NOT NULL,
    reason TEXT,
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    tax_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    total_refund_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    refund_method ENUM('CASH', 'UPI', 'CREDIT_NOTE') DEFAULT 'CASH',
    created_by_user_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE RESTRICT,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sales_return_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sales_return_id INT NOT NULL,
    sale_item_id INT NOT NULL,
    medicine_id INT NOT NULL,
    batch_id INT NOT NULL,
    quantity INT NOT NULL,
    refund_rate DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(12,2) NOT NULL,
    restock_status ENUM('RESTOCKED', 'DAMAGED_EXPIRED') DEFAULT 'RESTOCKED',
    FOREIGN KEY (sales_return_id) REFERENCES sales_returns(id) ON DELETE CASCADE,
    FOREIGN KEY (sale_item_id) REFERENCES sale_items(id) ON DELETE RESTRICT,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE RESTRICT,
    FOREIGN KEY (batch_id) REFERENCES medicine_batches(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 16. Stock Movements (Complete Audit of Every Single Inventory Change)
CREATE TABLE IF NOT EXISTS stock_movements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    batch_id INT NOT NULL,
    movement_type ENUM('PURCHASE', 'SALE', 'PURCHASE_RETURN', 'SALE_RETURN', 'ADJUSTMENT', 'EXPIRED_REMOVAL') NOT NULL,
    quantity_changed INT NOT NULL, -- positive for additions, negative for deductions
    previous_quantity INT NOT NULL,
    new_quantity INT NOT NULL,
    reference_type VARCHAR(50), -- e.g. 'SALE', 'PURCHASE', 'RETURN'
    reference_id INT NULL,      -- ID of sale, purchase, or return
    notes TEXT,
    user_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE RESTRICT,
    FOREIGN KEY (batch_id) REFERENCES medicine_batches(id) ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_movement_med (medicine_id),
    INDEX idx_movement_batch (batch_id),
    INDEX idx_movement_time (created_at)
) ENGINE=InnoDB;

-- 17. Operating Expenses
CREATE TABLE IF NOT EXISTS expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    expense_category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    expense_date DATE NOT NULL,
    payment_method ENUM('CASH', 'UPI', 'BANK_TRANSFER', 'CHEQUE') DEFAULT 'CASH',
    receipt_reference VARCHAR(100),
    user_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_expense_date (expense_date)
) ENGINE=InnoDB;

-- 18. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    username VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    module VARCHAR(50) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_module (module),
    INDEX idx_audit_time (created_at)
) ENGINE=InnoDB;

-- 19. Notification Logs
CREATE TABLE IF NOT EXISTS notification_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL, -- 'LOW_STOCK', 'EXPIRY', 'DAILY_SALES', 'EMAIL_REPORT'
    recipient VARCHAR(150),
    subject VARCHAR(255),
    message TEXT,
    status ENUM('SENT', 'FAILED', 'QUEUED') DEFAULT 'SENT',
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notif_type (notification_type),
    INDEX idx_notif_time (sent_at)
) ENGINE=InnoDB;
