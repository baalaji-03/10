# Baalaji Pharmacy Management System 💊

A modern, full-stack, enterprise-grade **Pharmacy Management System** designed for real-world pharmacy and retail chemist operations in India. It seamlessly supports both a **responsive Web application** and a **Windows Desktop application (Electron)**, sharing the same unified Python FastAPI backend and MySQL database.

---

## 🌟 Key Capabilities & Module Overview

### 1. Fast POS GST Billing
- **Lightning-Fast Keyboard-Friendly Checkout**: Search by brand name, generic salt, or instant barcode scan (`F2` search, `F4` customer, `F9` checkout).
- **Batch Tracking & Expiry Block**: Shows active batches with MRP and expiry date. **Strictly blocks sales of expired batches**.
- **Automated GST Engine**: Dynamically calculates CGST, SGST, or IGST based on item-level tax slabs (0%, 5%, 12%, 18%).
- **Atomic Stock Deduction**: Prevents race conditions and negative inventory using ACID database transactions.
- **Customer Integration**: Instant selection or auto-registration of walk-in or returning customers by mobile number.

### 2. Multi-Format Professional Bill Printing
- **58 mm Thermal Receipts**: Compact format for counter POS thermal printers.
- **80 mm Thermal Receipts**: Standard receipt format with itemized tax and pharmacist declarations.
- **A4 Full-Page Tax Invoices**: Standard corporate tax invoice layout with GSTIN, D.L. numbers, terms, and authorized signatory line.
- **Download as PDF**: Server-side vector PDF generation powered by **ReportLab**.
- **Instant Reprint**: Access and reprint any past invoice directly from Dashboard, POS, or Customer history.

### 3. Expiry Radar & Quarantine System
- **6-Month Horizon Watchlist**: Color-coded alert radar (🟠 Orange for batches expiring within 6 calendar months).
- **Expired Batch Quarantine**: Automatically highlights expired batches (🔴 Red Alert) and disables them from billing.
- **Stock Value Risk**: Computes total capital tied up in expiring/expired medicines based on actual purchase costs.
- **Export & Email**: Daily automated expiry report dispatch to manager's email with Excel attachment.

### 4. Low-Stock & Intelligent Reordering
- Configurable minimum safety stock level per product.
- Automatic calculation of **Suggested Reorder Quantity** based on configurable multiplier rules.
- Instant purchase order draft creation directly from the alert screen.

### 5. Multi-Item Purchase Entry & Supplier Ledger
- Supplier invoice entry with duplicate invoice prevention.
- Attach and download supplier bills (PDF, JPG, or PNG, up to 4 MB) from purchase entry or purchase details.
- Item-level quantity, free goods (`10+1` schemes), discounts, and input tax credit (ITC) calculations.
- Inventory is updated only upon purchase confirmation.
- Complete supplier ledger tracking payments, cheques, NEFT/RTGS references, and outstanding balances.

### 6. Excel Import & Export (openpyxl)
- **1-Click Export to Excel**:
  - Current Inventory & Rack Locations
  - Batches & Expiry Dates
  - Low-Stock Alarms
  - Daily, Weekly & Monthly Sales Reports
  - GSTR-1 Tax Summary (B2B / B2C breakdown)
  - Supplier Ledgers & Purchase History
- **Validated Excel Upload**:
  - Bulk medicine catalog upload with template validation.
  - Interactive preview table with error checking before committing to the database.

### 7. Automated Email Notifications (SMTP)
- Configurable SMTP settings with secure TLS/SSL.
- One-click **"Send Test Email"** button.
- On-demand and scheduled dispatch of:
  - Low-stock alerts with Excel attachments
  - Expiry radar reports with Excel attachments
  - Daily sales summaries with revenue and bill count

### 8. Financial, Profit & GST Analytics
- **Cost of Goods Sold (COGS)**: Calculated from the exact purchase cost of each sold batch.
- **Estimated Gross Profit & Margin %**: Live profit tracking on the dashboard.
- **Net Profit**: Deducts operational expenses (rent, electricity, staff salary).
- **GST Liability**: Computes Output GST minus Input Tax Credit (ITC).

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend** | HTML5, Modern CSS3 (Medical Design Tokens), Vanilla JavaScript (Modular ES6) |
| **Desktop App** | Electron 33, Electron-Builder (Windows NSIS `.exe` installer) |
| **Backend API** | Python 3.10+ / 3.14+, FastAPI, Uvicorn, Pydantic v2 |
| **Database** | MySQL 8.0+ (with resilient auto-fallback to SQLite for standalone zero-config dev) |
| **ORM & Data** | SQLAlchemy 2.0, PyMySQL |
| **PDF Engine** | ReportLab |
| **Spreadsheets** | openpyxl |
| **Visual Charts** | Chart.js 4.4 |
| **Email** | Python smtplib with MIME multipart attachments |
| **Test Suite** | pytest, pytest-asyncio, HTTPX |

## Deploying to Vercel

This project uses two Vercel services on one domain: a static frontend service
rooted at `frontend/`, and a FastAPI backend service rooted at the repository
root. The frontend calls `/api/...` on the same domain; Vercel routes those paths
to the backend and sends other paths to the frontend. There are no service
bindings because browser requests use the public `/api` route rather than
server-to-server calls.

Import the repository into Vercel with the repository root as the project root.
Add these environment variables to the Vercel project before deploying:

- `DATABASE_URL`: a connection URL for a persistent, externally hosted MySQL
  database (for example, `mysql+pymysql://user:password@host:3306/database`).
  Vercel's local filesystem and SQLite database are not persistent.
- `JWT_SECRET_KEY`: a long, randomly generated secret used to sign login tokens.

Purchase bill uploads are stored in MySQL so they persist across serverless
function invocations. The upload limit is 4 MB to stay within Vercel's request
body limit. After setting the environment variables, deploy or redeploy the
project; Vercel will install the root `requirements.txt`.

---

## 📁 Project Directory Structure

```
baalaji/
├── backend/
│   ├── app/
│   │   ├── config.py             # Settings, paths, secrets, database configuration
│   │   ├── database.py           # SQLAlchemy engine (MySQL + SQLite fallback)
│   │   ├── models.py             # Normalized ORM tables (20+ entities)
│   │   ├── schemas.py            # Pydantic v2 validation schemas
│   │   ├── auth.py               # Bcrypt password hashing & JWT RBAC
│   │   ├── seed.py               # Seed data generator for users, settings & sample catalog
│   │   ├── main.py               # FastAPI application entrypoint & static mounts
│   │   ├── services/
│   │   │   ├── invoice_service.py # ReportLab PDF invoice generator (A4, 80mm, 58mm)
│   │   │   ├── excel_service.py   # openpyxl import/export engine
│   │   │   └── email_service.py   # SMTP notifications with Excel attachments
│   │   └── routers/              # Modular API endpoints
│   │       ├── auth.py
│   │       ├── dashboard.py
│   │       ├── medicines.py
│   │       ├── purchases.py
│   │       ├── pos.py
│   │       ├── customers.py
│   │       ├── suppliers.py
│   │       ├── alerts.py
│   │       ├── returns.py
│   │       ├── reports.py
│   │       ├── expenses.py
│   │       ├── excel.py
│   │       ├── invoices.py
│   │       └── settings.py
│   ├── tests/
│   │   └── test_pharmacy.py      # Automated Pytest suite (Billing, Expiry block, Stock, Returns)
│   └── requirements.txt
├── database/
│   ├── schema.sql                # Production MySQL schema DDL
│   └── seed_data.sql             # SQL seed dataset
├── frontend/
│   ├── index.html                # Single-Page Application interface
│   ├── css/
│   │   ├── styles.css            # Medical UI design system & responsive layout
│   │   └── print.css             # Dedicated thermal receipt & A4 print CSS
│   ├── js/                       # Modular frontend controllers
│   │   ├── api.js                # API client with JWT interceptor
│   │   ├── auth.js               # Login & role-based view visibility
│   │   ├── dashboard.js          # Chart.js & KPI widgets
│   │   ├── pos.js                # Keyboard POS & barcode billing
│   │   ├── medicines.js          # Medicine & batch manager
│   │   ├── purchases.js          # Purchase entry form
│   │   ├── suppliers.js          # Supplier directory & payment ledger
│   │   ├── customers.js          # Customer records & history drawer
│   │   ├── alerts.js             # Expiry radar & low stock
│   │   ├── reports.js            # Financial & GST summaries
│   │   ├── returns.js            # Sales returns & credit notes
│   │   ├── settings.js           # Pharmacy details & SMTP test
│   │   ├── invoices.js           # Thermal & A4 print preview
│   │   └── app.js                # Lifecycle & modal manager
│   └── assets/
│       └── logo.svg              # Pharmacy cross branding
├── desktop/
│   ├── main.js                   # Electron main process (IPC thermal print & auto backend spawn)
│   ├── preload.js                # Secure IPC bridge
│   └── package.json              # Electron configuration & NSIS builder setup
├── .env.example                  # Environment template
├── init_db.py                    # Database creation & seeding script
├── run_web.bat                   # 1-Click launcher for Web Application
├── run_desktop.bat               # 1-Click launcher for Electron Desktop App
├── build_desktop.bat             # Standalone Windows installer builder (.exe)
└── README.md
```

---

## 🚀 Quick Start Guide (Windows)

### 1. Prerequisites
- **Python**: 3.10 or higher (Python 3.14 recommended).
- **Node.js**: v18 or higher (for the Electron desktop app).
- **MySQL**: (Optional for production; if MySQL is not running, the application gracefully uses SQLite automatically so you can test immediately with zero setup).

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
To connect to MySQL, adjust the credentials in `.env`:
```ini
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=pharmacy_db
```

### 3. Install Python Dependencies
```powershell
python -m pip install -r backend/requirements.txt
```

### 4. Initialize Database
Run the database setup script to create tables and seed default roles, settings, and demo catalog:
```powershell
python init_db.py
```

### 5. Run the Automated Tests
Verify all core billing rules, atomic stock deductions, and safety blocks:
```powershell
python -m pytest backend/tests/test_pharmacy.py -v
```

---

## 🖥️ Running the Application

### Option A: Web Application
Double-click **`run_web.bat`** or run:
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser at **`http://127.0.0.1:8000`**.

### Option B: Windows Desktop Application (Electron)
Double-click **`run_desktop.bat`** or run:
```powershell
npm.cmd install
npx.cmd electron desktop
```
*Note: The Electron desktop app automatically verifies and starts the Python backend server in the background if it is not already running!*

### Option C: Build Standalone Windows Installer (`.exe`)
Double-click **`build_desktop.bat`** or run:
```powershell
cd desktop
npm.cmd install
npm.cmd run build:win
```
The generated installer will be saved in `desktop\dist\Baalaji Pharmacy Management System Setup 1.0.0.exe`.

---

## 🔑 Default Login Credentials

| Role | Username | Password | Permitted Modules |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@123` | Full access across all modules, reports, users, settings |
| **Pharmacist** | `pharmacist` | `Admin@123` | POS Billing, Medicines, Batches, Purchases, Expiry Alerts |
| **Cashier** | `cashier` | `Admin@123` | Dedicated fast POS Billing, Customers, Invoice Reprint |
| **Inventory Staff** | `inventory` | `Admin@123` | Stock Entry, Purchases, Suppliers, Stock Movement Audit |

---

## 🔒 Pharmacy Network & Production Security Guide

1. **Local Network Deployment (LAN)**:
   - Run the FastAPI server on your designated pharmacy cashier server machine:
     ```powershell
     python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
     ```
   - Other counter terminals (web browsers or Electron desktops) on the same local network can connect via `http://<SERVER_IP>:8000`.
   - Never expose port 3306 (MySQL) directly over public WiFi or WAN. Bind MySQL only to `127.0.0.1` or the secure local subnet.
2. **Automated Database Backups**:
   - Create a daily Windows Task Scheduler job running `mysqldump`:
     ```powershell
     mysqldump -u root -p pharmacy_db > "C:\Backups\pharmacy_backup_%DATE%.sql"
     ```
3. **Data Integrity & Audit**:
   - Every sale, purchase, stock adjustment, and login event is recorded in the `audit_logs` and `stock_movements` tables for compliance with drug regulatory norms.
