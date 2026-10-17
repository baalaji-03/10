from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.app.models import (
    Role, User, PharmacySetting, Supplier, Medicine, MedicineBatch, StockMovement
)
from backend.app.auth import hash_password

def seed_database_defaults(db: Session):
    """
    Seeds initial default data if database tables are empty.
    """
    # 1. Seed Roles
    existing_roles = {r.name: r for r in db.query(Role).all()}
    roles_to_seed = [
        ("Admin", "Full administrative access across all modules"),
        ("Pharmacist", "Billing, medicine registry, inventory, and purchases"),
        ("Cashier", "Fast POS billing, customer registration, receipt reprint"),
        ("Inventory Staff", "Stock entry, supplier management, and inventory audit"),
    ]
    for r_name, r_desc in roles_to_seed:
        if r_name not in existing_roles:
            role = Role(name=r_name, description=r_desc)
            db.add(role)
    db.commit()

    # 2. Seed Pharmacy Setting
    setting = db.query(PharmacySetting).first()
    if not setting:
        setting = PharmacySetting(
            id=1,
            pharmacy_name="Baalaji Medicals & Healthcare",
            tagline="Your Trusted 24x7 Neighborhood Pharmacy",
            address_line1="No. 45, G.S.T. Road, Tambaram Sanatorium",
            address_line2="Opposite Government Hospital",
            city="Chennai",
            state="Tamil Nadu",
            postal_code="600047",
            phone="+91 94440 12345",
            email="care@baalajimedicals.com",
            gstin="33AAAAA9876B1Z8",
            dl_number="TN-CHE-20B-78901, TN-CHE-21B-78902",
            pan_number="AAAAA9876B",
            state_code="33",
            invoice_prefix="BM",
            invoice_declaration="1. Goods once sold will not be taken back without original bill.\n2. Prescribed medicines will not be dispensed without a valid doctor prescription.\n3. Storage instructions: Store below 25°C in a dry place.",
            currency_symbol="₹",
            expiry_warning_months=6,
            default_reorder_multiplier=2.00
        )
        db.add(setting)
        db.commit()

    # 3. Seed Users
    admin_user = db.query(User).filter(User.username == "admin").first()
    default_pwd_hash = hash_password("Admin@123")
    if not admin_user:
        users = [
            User(username="admin", email="admin@baalajimedicals.com", full_name="System Administrator", password_hash=default_pwd_hash, role="Admin", is_active=True),
            User(username="pharmacist", email="pharma@baalajimedicals.com", full_name="K. Baalaji, B.Pharm", password_hash=default_pwd_hash, role="Pharmacist", is_active=True),
            User(username="cashier", email="billing@baalajimedicals.com", full_name="M. Saravanan", password_hash=default_pwd_hash, role="Cashier", is_active=True),
            User(username="inventory", email="store@baalajimedicals.com", full_name="R. Suresh", password_hash=default_pwd_hash, role="Inventory Staff", is_active=True),
        ]
        db.add_all(users)
        db.commit()

    # 4. Seed Suppliers
    if db.query(Supplier).count() == 0:
        suppliers = [
            Supplier(supplier_code="SUP-001", name="Apollo Med Wholesale Ltd", contact_person="Ramanathan", phone="+91 98401 22334", email="orders@apollomedwholesale.com", gstin="33AAACA1234D1Z1", address="44 Industrial Estate, Guindy", city="Chennai", state="Tamil Nadu", dl_number="TN-CHE-20B-33445", outstanding_balance=12500.00),
            Supplier(supplier_code="SUP-002", name="Sun Pharma Distribution Hub", contact_person="Venkatesh S", phone="+91 97910 88990", email="southhub@sunpharma.com", gstin="33AABCS5678E1Z9", address="12 Ring Road Logistics Park", city="Chennai", state="Tamil Nadu", dl_number="TN-CHE-21B-99887", outstanding_balance=0.00),
            Supplier(supplier_code="SUP-003", name="Cipla Care Agencies", contact_person="Meenakshi Sundaram", phone="+91 94432 11002", email="chennaidist@ciplacare.com", gstin="33AACCC9012F1Z4", address="77 Mount Road, Teynampet", city="Chennai", state="Tamil Nadu", dl_number="TN-CHE-20B-66554", outstanding_balance=4500.00),
        ]
        db.add_all(suppliers)
        db.commit()

    # 5. Seed Medicines & Batches
    if db.query(Medicine).count() == 0:
        med_samples = [
            {"item_code": "MED-0001", "barcode": "8901088001122", "name": "Dolo 650mg Tablet", "generic_name": "Paracetamol 650mg", "manufacturer": "Micro Labs Ltd", "category": "Analgesic / Antipyretic", "hsn_code": "3004", "gst_rate": 12.00, "rack_location": "Rack-A1", "unit": "Strip (15 Tab)", "min_stock_level": 20, "purchase_price": 24.50, "selling_price": 33.60, "mrp": 33.60, "qty": 120, "batch": "DL2026A", "expiry": date.today() + timedelta(days=600), "status": "AVAILABLE"},
            {"item_code": "MED-0002", "barcode": "8901148002233", "name": "Augmentin 625 Duo", "generic_name": "Amoxicillin + Clavulanic Acid 625mg", "manufacturer": "GlaxoSmithKline", "category": "Antibiotic", "hsn_code": "3004", "gst_rate": 12.00, "rack_location": "Rack-B3", "unit": "Strip (10 Tab)", "min_stock_level": 15, "purchase_price": 145.00, "selling_price": 201.50, "mrp": 201.50, "qty": 4, "batch": "AG9901B", "expiry": date.today() + timedelta(days=400), "status": "LOW_STOCK"},
            {"item_code": "MED-0003", "barcode": "8901234003344", "name": "Pan 40 Tablet", "generic_name": "Pantoprazole 40mg", "manufacturer": "Alkem Laboratories", "category": "Gastrointestinal", "hsn_code": "3004", "gst_rate": 12.00, "rack_location": "Rack-A3", "unit": "Strip (15 Tab)", "min_stock_level": 25, "purchase_price": 95.00, "selling_price": 155.00, "mrp": 155.00, "qty": 80, "batch": "PAN8811", "expiry": date.today() + timedelta(days=500), "status": "AVAILABLE"},
            {"item_code": "MED-0004", "barcode": "8901345004455", "name": "Azithral 500mg", "generic_name": "Azithromycin 500mg", "manufacturer": "Alembic Pharma", "category": "Antibiotic", "hsn_code": "3004", "gst_rate": 12.00, "rack_location": "Rack-B1", "unit": "Strip (5 Tab)", "min_stock_level": 10, "purchase_price": 82.00, "selling_price": 119.50, "mrp": 119.50, "qty": 18, "batch": "AZ6060X", "expiry": date.today() + timedelta(days=55), "status": "AVAILABLE"},  # Near Expiry < 6 months!
            {"item_code": "MED-0005", "barcode": "8901456005566", "name": "Glycomet GP 1", "generic_name": "Glimepiride 1mg + Metformin 500mg", "manufacturer": "USV Private Ltd", "category": "Antidiabetic", "hsn_code": "3004", "gst_rate": 12.00, "rack_location": "Rack-C2", "unit": "Strip (15 Tab)", "min_stock_level": 30, "purchase_price": 85.00, "selling_price": 128.00, "mrp": 128.00, "qty": 22, "batch": "GLY4420", "expiry": date.today() + timedelta(days=120), "status": "AVAILABLE"}, # Near Expiry < 6 months!
            {"item_code": "MED-0006", "barcode": "8901567006677", "name": "Telma 40 Tablet", "generic_name": "Telmisartan 40mg", "manufacturer": "Glenmark Pharma", "category": "Cardiovascular", "hsn_code": "3004", "gst_rate": 12.00, "rack_location": "Rack-C4", "unit": "Strip (30 Tab)", "min_stock_level": 15, "purchase_price": 180.00, "selling_price": 260.00, "mrp": 260.00, "qty": 50, "batch": "TEL3030", "expiry": date.today() + timedelta(days=700), "status": "AVAILABLE"},
            {"item_code": "MED-0007", "barcode": "8901678007788", "name": "Montair LC Tablet", "generic_name": "Levocetirizine + Montelukast", "manufacturer": "Cipla Ltd", "category": "Respiratory / Antiallergic", "hsn_code": "3004", "gst_rate": 12.00, "rack_location": "Rack-D1", "unit": "Strip (10 Tab)", "min_stock_level": 20, "purchase_price": 130.00, "selling_price": 198.00, "mrp": 198.00, "qty": 15, "batch": "MNT1009", "expiry": date.today() - timedelta(days=45), "status": "EXPIRED"}, # Already expired!
            {"item_code": "MED-0008", "barcode": "8901789008899", "name": "Becosules Z Capsules", "generic_name": "Vitamin B-Complex with Zinc", "manufacturer": "Pfizer India", "category": "Vitamins & Supplements", "hsn_code": "3004", "gst_rate": 12.00, "rack_location": "Rack-E2", "unit": "Strip (20 Cap)", "min_stock_level": 25, "purchase_price": 32.00, "selling_price": 48.00, "mrp": 48.00, "qty": 95, "batch": "BEC7788", "expiry": date.today() + timedelta(days=650), "status": "AVAILABLE"},
            {"item_code": "MED-0009", "barcode": "8901890009900", "name": "Shelcal 500 Tablet", "generic_name": "Calcium 500mg + Vitamin D3", "manufacturer": "Torrent Pharma", "category": "Minerals & Supplements", "hsn_code": "3004", "gst_rate": 12.00, "rack_location": "Rack-E4", "unit": "Strip (15 Tab)", "min_stock_level": 15, "purchase_price": 88.00, "selling_price": 131.00, "mrp": 131.00, "qty": 60, "batch": "SHL5544", "expiry": date.today() + timedelta(days=620), "status": "AVAILABLE"},
            {"item_code": "MED-0010", "barcode": "8901901010011", "name": "Vicks Vaporub 25g", "generic_name": "Menthol, Camphor, Eucalyptus", "manufacturer": "Procter & Gamble", "category": "OTC Balms", "hsn_code": "3004", "gst_rate": 18.00, "rack_location": "Front Counter", "unit": "Jar", "min_stock_level": 10, "purchase_price": 68.00, "selling_price": 95.00, "mrp": 95.00, "qty": 35, "batch": "VK0909A", "expiry": date.today() + timedelta(days=800), "status": "AVAILABLE"},
        ]

        for item in med_samples:
            med = Medicine(
                item_code=item["item_code"],
                barcode=item["barcode"],
                name=item["name"],
                generic_name=item["generic_name"],
                manufacturer=item["manufacturer"],
                category=item["category"],
                hsn_code=item["hsn_code"],
                gst_rate=item["gst_rate"],
                rack_location=item["rack_location"],
                unit=item["unit"],
                min_stock_level=item["min_stock_level"],
                default_purchase_price=item["purchase_price"],
                default_selling_price=item["selling_price"],
                is_prescription_required=False,
                is_active=True
            )
            db.add(med)
            db.flush()

            batch = MedicineBatch(
                medicine_id=med.id,
                batch_number=item["batch"],
                manufacturing_date=date.today() - timedelta(days=180),
                expiry_date=item["expiry"],
                purchase_price=item["purchase_price"],
                mrp=item["mrp"],
                selling_price=item["selling_price"],
                quantity=item["qty"],
                supplier_id=1,
                status=item["status"]
            )
            db.add(batch)
            db.flush()

            movement = StockMovement(
                medicine_id=med.id,
                batch_id=batch.id,
                movement_type="PURCHASE",
                quantity_changed=item["qty"],
                previous_quantity=0,
                new_quantity=item["qty"],
                reference_type="INITIAL_SETUP",
                notes="Initial inventory setup"
            )
            db.add(movement)

        db.commit()
