from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, Date, Time, DateTime,
    ForeignKey, Text, Numeric, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from sqlalchemy import LargeBinary
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from backend.app.database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=func.now())

    users = relationship("User", back_populates="role_obj")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(String(255))

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="Pharmacist")  # Admin, Pharmacist, Cashier, Inventory Staff
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    role_obj = relationship("Role", back_populates="users")
    sales = relationship("Sale", back_populates="user")

class PharmacySetting(Base):
    __tablename__ = "pharmacy_settings"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_name = Column(String(150), default="Baalaji Medicals & Pharmacy")
    tagline = Column(String(200), default="Care, Trust & Wellness")
    address_line1 = Column(String(255), default="123 Cross Road, Anna Nagar")
    address_line2 = Column(String(255), default="Main Commercial Complex")
    city = Column(String(100), default="Chennai")
    state = Column(String(100), default="Tamil Nadu")
    postal_code = Column(String(20), default="600040")
    phone = Column(String(30), default="+91 98765 43210")
    email = Column(String(100), default="info@baalajipharmacy.com")
    gstin = Column(String(30), default="33AAAAA0000A1Z5")
    dl_number = Column(String(100), default="DL-TN-20B-12345, 21B-12346")
    pan_number = Column(String(30), default="AAAAA0000A")
    state_code = Column(String(10), default="33")
    invoice_prefix = Column(String(10), default="INV")
    invoice_declaration = Column(Text, default="1. Goods once sold will not be taken back without original bill.\n2. Prescribed medicines will not be dispensed without a valid prescription.")
    currency_symbol = Column(String(10), default="₹")
    
    # SMTP Email Settings
    smtp_host = Column(String(150), default="")
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(100), default="")
    smtp_password = Column(String(255), default="")
    smtp_use_tls = Column(Boolean, default=True)
    smtp_from_email = Column(String(100), default="")
    alert_email_recipient = Column(String(200), default="")
    
    # Automation & Alerts
    expiry_warning_months = Column(Integer, default=6)
    default_reorder_multiplier = Column(Numeric(5, 2), default=2.00)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(30), unique=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    mobile = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), default="Other")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    sales = relationship("Sale", back_populates="customer")

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_code = Column(String(30), unique=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    contact_person = Column(String(100))
    phone = Column(String(30), nullable=False)
    email = Column(String(100))
    gstin = Column(String(30))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    state_code = Column(String(10), default="33")
    dl_number = Column(String(100))
    pan_number = Column(String(30))
    outstanding_balance = Column(Numeric(12, 2), default=0.00)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    purchases = relationship("Purchase", back_populates="supplier")
    batches = relationship("MedicineBatch", back_populates="supplier")

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(50), unique=True, index=True)
    barcode = Column(String(100), unique=True, index=True, nullable=True)
    name = Column(String(200), nullable=False, index=True)
    generic_name = Column(String(200), index=True)
    manufacturer = Column(String(150))
    category = Column(String(100), default="Allopathy")
    hsn_code = Column(String(20), default="3004")
    gst_rate = Column(Numeric(5, 2), default=12.00)
    rack_location = Column(String(50))
    unit = Column(String(20), default="Strip")
    min_stock_level = Column(Integer, default=10)
    default_purchase_price = Column(Numeric(10, 2), default=0.00)
    default_selling_price = Column(Numeric(10, 2), default=0.00)
    is_prescription_required = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    batches = relationship("MedicineBatch", back_populates="medicine", cascade="all, delete-orphan")
    sale_items = relationship("SaleItem", back_populates="medicine")
    stock_movements = relationship("StockMovement", back_populates="medicine")

class MedicineBatch(Base):
    __tablename__ = "medicine_batches"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_number = Column(String(100), nullable=False, index=True)
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False, index=True)
    purchase_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    mrp = Column(Numeric(10, 2), nullable=False, default=0.00)
    selling_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    quantity = Column(Integer, nullable=False, default=0)
    free_quantity = Column(Integer, default=0)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), default="AVAILABLE")  # AVAILABLE, LOW_STOCK, EXPIRED, QUARANTINED, DEPLETED
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("medicine_id", "batch_number", name="uk_medicine_batch"),
    )

    medicine = relationship("Medicine", back_populates="batches")
    supplier = relationship("Supplier", back_populates="batches")
    sale_items = relationship("SaleItem", back_populates="batch")
    stock_movements = relationship("StockMovement", back_populates="batch")

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    purchase_number = Column(String(50), unique=True, index=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    supplier_invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(Date, nullable=False, index=True)
    received_date = Column(Date, nullable=False)
    subtotal = Column(Numeric(12, 2), default=0.00)
    discount_amount = Column(Numeric(12, 2), default=0.00)
    cgst_amount = Column(Numeric(12, 2), default=0.00)
    sgst_amount = Column(Numeric(12, 2), default=0.00)
    igst_amount = Column(Numeric(12, 2), default=0.00)
    tax_amount = Column(Numeric(12, 2), default=0.00)
    additional_charges = Column(Numeric(12, 2), default=0.00)
    round_off = Column(Numeric(6, 2), default=0.00)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    paid_amount = Column(Numeric(12, 2), default=0.00)
    balance_amount = Column(Numeric(12, 2), default=0.00)
    payment_status = Column(String(20), default="PENDING")  # PENDING, PARTIAL, PAID
    status = Column(String(20), default="CONFIRMED")  # DRAFT, CONFIRMED, CANCELLED
    notes = Column(Text)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("supplier_id", "supplier_invoice_number", name="uk_supplier_invoice"),
    )

    supplier = relationship("Supplier", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    bill_attachment = relationship(
        "PurchaseBill", back_populates="purchase", uselist=False, cascade="all, delete-orphan"
    )

class PurchaseBill(Base):
    __tablename__ = "purchase_bills"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(
        Integer, ForeignKey("purchases.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(100), unique=True, nullable=False)
    content_type = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())

    purchase = relationship("Purchase", back_populates="bill_attachment")
    file_content = relationship(
        "PurchaseBillContent", back_populates="bill", uselist=False, cascade="all, delete-orphan"
    )

class PurchaseBillContent(Base):
    __tablename__ = "purchase_bill_contents"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(
        Integer, ForeignKey("purchase_bills.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    content = Column(LargeBinary().with_variant(MEDIUMBLOB(), "mysql"), nullable=False)

    bill = relationship("PurchaseBill", back_populates="file_content")

class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False)
    batch_id = Column(Integer, ForeignKey("medicine_batches.id", ondelete="SET NULL"), nullable=True)
    batch_number = Column(String(100), nullable=False)
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    free_quantity = Column(Integer, default=0)
    purchase_price = Column(Numeric(10, 2), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0.00)
    discount_amount = Column(Numeric(10, 2), default=0.00)
    gst_rate = Column(Numeric(5, 2), default=12.00)
    cgst_rate = Column(Numeric(5, 2), default=6.00)
    sgst_rate = Column(Numeric(5, 2), default=6.00)
    igst_rate = Column(Numeric(5, 2), default=0.00)
    cgst_amount = Column(Numeric(10, 2), default=0.00)
    sgst_amount = Column(Numeric(10, 2), default=0.00)
    igst_amount = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(12, 2), nullable=False)

    purchase = relationship("Purchase", back_populates="items")
    medicine = relationship("Medicine")

class SupplierPayment(Base):
    __tablename__ = "supplier_payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="SET NULL"), nullable=True)
    payment_date = Column(Date, nullable=False, default=date.today)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(30), default="BANK_TRANSFER")
    reference_number = Column(String(100))
    notes = Column(Text)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=func.now())

    supplier = relationship("Supplier")

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_name = Column(String(100), default="Walk-in Customer")
    customer_mobile = Column(String(20), nullable=True)
    doctor_name = Column(String(100), nullable=True)
    invoice_date = Column(Date, nullable=False, default=date.today, index=True)
    invoice_time = Column(Time, nullable=False, default=lambda: datetime.now().time())
    subtotal = Column(Numeric(12, 2), default=0.00)
    discount_amount = Column(Numeric(12, 2), default=0.00)
    taxable_amount = Column(Numeric(12, 2), default=0.00)
    cgst_amount = Column(Numeric(12, 2), default=0.00)
    sgst_amount = Column(Numeric(12, 2), default=0.00)
    igst_amount = Column(Numeric(12, 2), default=0.00)
    tax_amount = Column(Numeric(12, 2), default=0.00)
    round_off = Column(Numeric(6, 2), default=0.00)
    net_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    paid_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    balance_amount = Column(Numeric(12, 2), default=0.00)
    payment_method = Column(String(20), default="CASH")  # CASH, UPI, CARD, CREDIT, MIXED
    payment_status = Column(String(20), default="PAID")  # PAID, PARTIAL, CREDIT
    status = Column(String(20), default="COMPLETED")  # COMPLETED, CANCELLED, RETURNED
    total_cost_of_goods = Column(Numeric(12, 2), default=0.00)
    gross_profit = Column(Numeric(12, 2), default=0.00)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="sales")
    user = relationship("User", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="sale", cascade="all, delete-orphan")

class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False)
    batch_id = Column(Integer, ForeignKey("medicine_batches.id", ondelete="RESTRICT"), nullable=False)
    medicine_name = Column(String(200), nullable=False)
    generic_name = Column(String(200))
    batch_number = Column(String(100), nullable=False)
    expiry_date = Column(Date, nullable=False)
    hsn_code = Column(String(20), default="3004")
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    purchase_price = Column(Numeric(10, 2), default=0.00)
    mrp = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0.00)
    discount_amount = Column(Numeric(10, 2), default=0.00)
    taxable_amount = Column(Numeric(10, 2), nullable=False)
    gst_rate = Column(Numeric(5, 2), default=12.00)
    cgst_rate = Column(Numeric(5, 2), default=6.00)
    sgst_rate = Column(Numeric(5, 2), default=6.00)
    igst_rate = Column(Numeric(5, 2), default=0.00)
    cgst_amount = Column(Numeric(10, 2), default=0.00)
    sgst_amount = Column(Numeric(10, 2), default=0.00)
    igst_amount = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(12, 2), nullable=False)
    cost_amount = Column(Numeric(12, 2), default=0.00)
    profit_amount = Column(Numeric(12, 2), default=0.00)

    sale = relationship("Sale", back_populates="items")
    medicine = relationship("Medicine", back_populates="sale_items")
    batch = relationship("MedicineBatch", back_populates="sale_items")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    payment_method = Column(String(20), default="CASH")
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_ref = Column(String(100))
    payment_date = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    sale = relationship("Sale", back_populates="payments")

class PurchaseReturn(Base):
    __tablename__ = "purchase_returns"

    id = Column(Integer, primary_key=True, index=True)
    return_number = Column(String(50), unique=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="SET NULL"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    return_date = Column(Date, default=date.today)
    reason = Column(Text)
    subtotal = Column(Numeric(12, 2), default=0.00)
    tax_amount = Column(Numeric(12, 2), default=0.00)
    total_refund_amount = Column(Numeric(12, 2), default=0.00)
    status = Column(String(20), default="COMPLETED")
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=func.now())

    supplier = relationship("Supplier")
    items = relationship("PurchaseReturnItem", back_populates="purchase_return", cascade="all, delete-orphan")

class PurchaseReturnItem(Base):
    __tablename__ = "purchase_return_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_return_id = Column(Integer, ForeignKey("purchase_returns.id", ondelete="CASCADE"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False)
    batch_id = Column(Integer, ForeignKey("medicine_batches.id", ondelete="RESTRICT"), nullable=False)
    batch_number = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(12, 2), nullable=False)

    purchase_return = relationship("PurchaseReturn", back_populates="items")
    medicine = relationship("Medicine")
    batch = relationship("MedicineBatch")

class SalesReturn(Base):
    __tablename__ = "sales_returns"

    id = Column(Integer, primary_key=True, index=True)
    return_number = Column(String(50), unique=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    return_date = Column(Date, default=date.today)
    reason = Column(Text)
    subtotal = Column(Numeric(12, 2), default=0.00)
    tax_amount = Column(Numeric(12, 2), default=0.00)
    total_refund_amount = Column(Numeric(12, 2), default=0.00)
    refund_method = Column(String(20), default="CASH")
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=func.now())

    sale = relationship("Sale")
    customer = relationship("Customer")
    items = relationship("SalesReturnItem", back_populates="sales_return", cascade="all, delete-orphan")

class SalesReturnItem(Base):
    __tablename__ = "sales_return_items"

    id = Column(Integer, primary_key=True, index=True)
    sales_return_id = Column(Integer, ForeignKey("sales_returns.id", ondelete="CASCADE"), nullable=False)
    sale_item_id = Column(Integer, ForeignKey("sale_items.id", ondelete="RESTRICT"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False)
    batch_id = Column(Integer, ForeignKey("medicine_batches.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, nullable=False)
    refund_rate = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(12, 2), nullable=False)
    restock_status = Column(String(30), default="RESTOCKED")  # RESTOCKED or DAMAGED_EXPIRED

    sales_return = relationship("SalesReturn", back_populates="items")
    medicine = relationship("Medicine")
    batch = relationship("MedicineBatch")

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False)
    batch_id = Column(Integer, ForeignKey("medicine_batches.id", ondelete="RESTRICT"), nullable=False)
    movement_type = Column(String(50), nullable=False)  # PURCHASE, SALE, PURCHASE_RETURN, SALE_RETURN, ADJUSTMENT, EXPIRED_REMOVAL
    quantity_changed = Column(Integer, nullable=False)
    previous_quantity = Column(Integer, nullable=False)
    new_quantity = Column(Integer, nullable=False)
    reference_type = Column(String(50))  # SALE, PURCHASE, RETURN, ADJUSTMENT
    reference_id = Column(Integer, nullable=True)
    notes = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    medicine = relationship("Medicine", back_populates="stock_movements")
    batch = relationship("MedicineBatch", back_populates="stock_movements")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    expense_category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    expense_date = Column(Date, default=date.today, index=True)
    payment_method = Column(String(30), default="CASH")
    receipt_reference = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(100))
    action = Column(String(100), nullable=False)
    module = Column(String(50), nullable=False, index=True)
    details = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=func.now(), index=True)

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    recipient = Column(String(150))
    subject = Column(String(255))
    message = Column(Text)
    status = Column(String(20), default="SENT")
    error_message = Column(Text)
    sent_at = Column(DateTime, default=func.now(), index=True)
