import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import User, Medicine, MedicineBatch, Supplier, PharmacySetting
from backend.app.auth import hash_password

# Use an isolated SQLite in-memory/test database for tests
TEST_DATABASE_URL = "sqlite:///./test_pharmacy.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    # Seed initial test admin
    db = TestingSessionLocal()
    admin = User(
        username="testadmin",
        email="testadmin@baalajimedicals.com",
        full_name="Test Administrator",
        password_hash=hash_password("Admin@123"),
        role="Admin",
        is_active=True
    )
    db.add(admin)

    # Seed pharmacy setting
    setting = PharmacySetting(
        id=1,
        pharmacy_name="Baalaji Test Pharmacy",
        gstin="33TEST0000A1Z1",
        invoice_prefix="TEST",
        expiry_warning_months=6
    )
    db.add(setting)

    # Seed test supplier
    supplier = Supplier(
        id=1,
        supplier_code="SUP-TEST",
        name="Apollo Test Wholesale",
        phone="9876543210",
        outstanding_balance=0.0
    )
    db.add(supplier)
    db.flush()

    # Seed test medicine and batch
    med = Medicine(
        id=1,
        item_code="MED-TEST-01",
        name="Dolo 650mg Test",
        generic_name="Paracetamol",
        category="Analgesic",
        hsn_code="3004",
        gst_rate=12.0,
        min_stock_level=10,
        default_purchase_price=20.0,
        default_selling_price=30.0,
        is_active=True
    )
    db.add(med)
    db.flush()

    batch = MedicineBatch(
        id=1,
        medicine_id=1,
        batch_number="BATCH-DOLO",
        expiry_date=date.today() + timedelta(days=365),
        purchase_price=20.0,
        mrp=30.0,
        selling_price=30.0,
        quantity=50,
        supplier_id=1,
        status="AVAILABLE"
    )
    db.add(batch)

    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    login_resp = client.post("/api/auth/login", data={"username": "testadmin", "password": "Admin@123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ----------------- 1. Auth Test -----------------
def test_login_success_and_failure(client):
    # Valid login
    res = client.post("/api/auth/login", data={"username": "testadmin", "password": "Admin@123"})
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert res.json()["role"] == "Admin"

    # Invalid login
    res_bad = client.post("/api/auth/login", data={"username": "testadmin", "password": "WrongPassword"})
    assert res_bad.status_code == 401

def test_health_reports_database_startup_failure(monkeypatch):
    def fail_database_initialization(*args, **kwargs):
        raise SQLAlchemyError("test database unavailable")

    monkeypatch.setattr(Base.metadata, "create_all", fail_database_initialization)
    with TestClient(app) as test_client:
        response = test_client.get("/api/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] == "unavailable"

# ----------------- 2. Medicine & Batch Creation -----------------
def test_create_medicine_and_batch(client, auth_headers):
    # 1. Create Medicine with active batch
    future_date = (date.today() + timedelta(days=365)).isoformat()
    med_payload = {
        "name": "Paracetamol 500mg Test",
        "generic_name": "Paracetamol",
        "category": "Analgesic",
        "hsn_code": "3004",
        "gst_rate": 12.0,
        "min_stock_level": 10,
        "default_purchase_price": 20.0,
        "default_selling_price": 30.0,
        "initial_batch_number": "BATCH-P1",
        "expiry_date": future_date,
        "quantity": 50,
        "supplier_id": 1
    }
    res = client.post("/api/medicines", json=med_payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Paracetamol 500mg Test"
    assert data["total_stock"] == 50

# ----------------- 3. POS Billing & Stock Deduction -----------------
def test_pos_billing_atomic_deduction(client, auth_headers):
    # Find batch
    meds = client.get("/api/medicines?search=Paracetamol", headers=auth_headers).json()
    med = meds[0]
    batch = med["batches"][0]
    assert batch["quantity"] == 50

    # Bill 5 units
    bill_payload = {
        "customer_name": "Ravi Test",
        "customer_mobile": "9998887776",
        "payment_method": "CASH",
        "paid_amount": 168.0,
        "items": [
            {
                "medicine_id": med["id"],
                "batch_id": batch["id"],
                "quantity": 5,
                "unit_price": 30.0,
                "discount_percent": 0.0
            }
        ]
    }
    bill_res = client.post("/api/pos/sale", json=bill_payload, headers=auth_headers)
    assert bill_res.status_code == 200
    sale = bill_res.json()
    assert sale["net_amount"] > 0
    assert sale["invoice_number"].startswith("TEST-")

    # Verify atomic stock deduction
    meds_after = client.get("/api/medicines?search=Paracetamol", headers=auth_headers).json()
    batch_after = meds_after[0]["batches"][0]
    assert batch_after["quantity"] == 45  # 50 - 5 = 45!

# ----------------- 4. Safety: BLOCK EXPIRED BATCH SALE -----------------
def test_prevent_expired_batch_sale(client, auth_headers):
    # Create an expired batch
    meds = client.get("/api/medicines?search=Paracetamol", headers=auth_headers).json()
    med_id = meds[0]["id"]

    past_date = (date.today() - timedelta(days=30)).isoformat()
    exp_batch_payload = {
        "batch_number": "EXPIRED-B99",
        "expiry_date": past_date,
        "purchase_price": 20.0,
        "mrp": 30.0,
        "selling_price": 30.0,
        "quantity": 25,
        "supplier_id": 1
    }
    b_res = client.post(f"/api/medicines/{med_id}/batches", json=exp_batch_payload, headers=auth_headers)
    assert b_res.status_code == 200, f"Batch creation failed: {b_res.json()}"
    exp_batch_id = b_res.json()["id"]

    # Attempt to sell expired batch -> MUST BE STRICTLY REJECTED!
    bill_payload = {
        "customer_name": "Test Cust",
        "customer_mobile": "9990001112",
        "payment_method": "CASH",
        "items": [
            {
                "medicine_id": med_id,
                "batch_id": exp_batch_id,
                "quantity": 2,
                "unit_price": 30.0
            }
        ]
    }
    sale_attempt = client.post("/api/pos/sale", json=bill_payload, headers=auth_headers)
    assert sale_attempt.status_code == 400
    assert "expired" in sale_attempt.json()["detail"].lower()

# ----------------- 5. Safety: BLOCK INSUFFICIENT STOCK -----------------
def test_prevent_insufficient_stock_sale(client, auth_headers):
    meds = client.get("/api/medicines?search=Paracetamol", headers=auth_headers).json()
    med_id = meds[0]["id"]
    batch_id = meds[0]["batches"][0]["id"] # has 45 units

    bill_payload = {
        "customer_name": "Test Cust",
        "payment_method": "CASH",
        "items": [
            {
                "medicine_id": med_id,
                "batch_id": batch_id,
                "quantity": 9999, # Excess quantity
                "unit_price": 30.0
            }
        ]
    }
    res = client.post("/api/pos/sale", json=bill_payload, headers=auth_headers)
    assert res.status_code == 400
    assert "insufficient stock" in res.json()["detail"].lower()

# ----------------- 6. Purchase Entry & Duplicate Prevention -----------------
def test_purchase_entry_and_duplicate_check(client, auth_headers):
    pur_date = date.today().isoformat()
    future_date = (date.today() + timedelta(days=500)).isoformat()
    
    pur_payload = {
        "supplier_id": 1,
        "supplier_invoice_number": "INV-SUP-9999",
        "invoice_date": pur_date,
        "received_date": pur_date,
        "paid_amount": 500.0,
        "items": [
            {
                "medicine_name": "Amoxicillin 500mg Test",
                "batch_number": "AMX-888",
                "expiry_date": future_date,
                "quantity": 100,
                "free_quantity": 5,
                "purchase_price": 40.0,
                "mrp": 60.0,
                "selling_price": 60.0,
                "gst_rate": 12.0
            }
        ]
    }
    # First purchase succeeds
    res1 = client.post("/api/purchases", json=pur_payload, headers=auth_headers)
    assert res1.status_code == 200

    purchase_id = res1.json()["id"]
    pdf_content = b"%PDF-1.4\nSupplier invoice"
    upload_res = client.post(
        f"/api/purchases/{purchase_id}/bill",
        files={"file": ("supplier-invoice.pdf", pdf_content, "application/pdf")},
        headers=auth_headers
    )
    assert upload_res.status_code == 200
    assert upload_res.json()["filename"] == "supplier-invoice.pdf"

    detail_res = client.get(f"/api/purchases/{purchase_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["bill_filename"] == "supplier-invoice.pdf"

    download_res = client.get(f"/api/purchases/{purchase_id}/bill", headers=auth_headers)
    assert download_res.status_code == 200
    assert download_res.content == pdf_content
    assert download_res.headers["content-type"] == "application/pdf"

    invalid_upload = client.post(
        f"/api/purchases/{purchase_id}/bill",
        files={"file": ("supplier-invoice.pdf", b"<html>not a PDF</html>", "application/pdf")},
        headers=auth_headers
    )
    assert invalid_upload.status_code == 400

    # Duplicate supplier invoice for same supplier fails!
    res_dup = client.post("/api/purchases", json=pur_payload, headers=auth_headers)
    assert res_dup.status_code == 400
    assert "duplicate invoice" in res_dup.json()["detail"].lower()

# ----------------- 7. Sales Return & Restock -----------------
def test_sales_return_restock(client, auth_headers):
    # Get last invoice
    invoices = client.get("/api/pos/invoices", headers=auth_headers).json()
    last_sale_id = invoices[0]["id"]
    sale_detail = client.get(f"/api/pos/invoices/{last_sale_id}", headers=auth_headers).json()
    item = sale_detail["items"][0]

    # Return 2 units
    ret_payload = {
        "sale_id": last_sale_id,
        "reason": "Customer ordered excess",
        "refund_method": "CASH",
        "items": [
            {
                "sale_item_id": item["id"],
                "quantity": 2,
                "restock_status": "RESTOCKED"
            }
        ]
    }
    ret_res = client.post("/api/returns/sales", json=ret_payload, headers=auth_headers)
    assert ret_res.status_code == 200
    assert ret_res.json()["success"] is True

# ----------------- 8. GST Calculation Accuracy -----------------
def test_gst_reporting_calculations(client, auth_headers):
    report_res = client.get("/api/reports/financial", headers=auth_headers)
    assert report_res.status_code == 200
    data = report_res.json()
    assert "gst_summary" in data
    assert "output_tax" in data["gst_summary"]
    assert "cgst" in data["gst_summary"]["output_tax"]
    assert "sgst" in data["gst_summary"]["output_tax"]

# ----------------- 9. Supplier Payment & Ledger -----------------
def test_supplier_payment_and_balance(client, auth_headers):
    pay_payload = {
        "supplier_id": 1,
        "amount": 500.0,
        "payment_method": "BANK_TRANSFER",
        "reference_number": "UTR-123456",
        "notes": "Advance payment"
    }
    pay_res = client.post("/api/suppliers/payments", json=pay_payload, headers=auth_headers)
    assert pay_res.status_code == 200
    data = pay_res.json()
    assert data["success"] is True
    assert "payment_number" in data

    # Check ledger
    ledger_res = client.get("/api/suppliers/1/ledger", headers=auth_headers)
    assert ledger_res.status_code == 200
    ledger = ledger_res.json()
    assert ledger["supplier"]["id"] == 1
    assert len(ledger["payments"]) >= 1
    assert ledger["payments"][0]["payment_method"] == "BANK_TRANSFER"

# ----------------- 10. Customer Management -----------------
def test_customer_creation_and_search(client, auth_headers):
    cust_payload = {
        "name": "Ravi Kumar",
        "mobile": "9876500001",
        "email": "ravi@example.com",
        "address": "12 Gandhi Road, Chennai"
    }
    cust_res = client.post("/api/customers", json=cust_payload, headers=auth_headers)
    assert cust_res.status_code == 200
    cust_data = cust_res.json()
    assert cust_data["name"] == "Ravi Kumar"
    assert cust_data["mobile"] == "9876500001"

    # Search customer
    search_res = client.get("/api/customers?search=Ravi", headers=auth_headers)
    assert search_res.status_code == 200
    results = search_res.json()
    assert len(results) >= 1
    assert any(c["mobile"] == "9876500001" for c in results)
