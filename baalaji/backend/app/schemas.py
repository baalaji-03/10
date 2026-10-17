from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict

# ----------------- Auth Schemas -----------------
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    full_name: str
    role: str

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: str = "Pharmacist"
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- Pharmacy Settings -----------------
class PharmacySettingUpdate(BaseModel):
    pharmacy_name: str
    tagline: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    phone: str
    email: str
    gstin: str
    dl_number: str
    pan_number: Optional[str] = None
    state_code: str = "33"
    invoice_prefix: str = "INV"
    invoice_declaration: Optional[str] = None
    currency_symbol: str = "₹"
    smtp_host: Optional[str] = ""
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = ""
    smtp_password: Optional[str] = ""
    smtp_use_tls: Optional[bool] = True
    smtp_from_email: Optional[str] = ""
    alert_email_recipient: Optional[str] = ""
    expiry_warning_months: int = 6
    default_reorder_multiplier: float = 2.00

class PharmacySettingResponse(PharmacySettingUpdate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SmtpTestRequest(BaseModel):
    test_recipient: EmailStr

# ----------------- Customer Schemas -----------------
class CustomerBase(BaseModel):
    name: str
    mobile: str
    email: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = "Other"
    notes: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    notes: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: int
    customer_code: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- Supplier Schemas -----------------
class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: str
    email: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = "33"
    dl_number: Optional[str] = None
    pan_number: Optional[str] = None

class SupplierCreate(SupplierBase):
    opening_balance: Optional[float] = 0.00

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    dl_number: Optional[str] = None
    pan_number: Optional[str] = None
    is_active: Optional[bool] = None

class SupplierResponse(SupplierBase):
    id: int
    supplier_code: Optional[str] = None
    outstanding_balance: float
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SupplierPaymentCreate(BaseModel):
    supplier_id: int
    purchase_id: Optional[int] = None
    amount: float
    payment_date: Optional[date] = None
    payment_method: str = "BANK_TRANSFER"
    reference_number: Optional[str] = None
    notes: Optional[str] = None

# ----------------- Medicine & Batch Schemas -----------------
class BatchBase(BaseModel):
    batch_number: str
    manufacturing_date: Optional[date] = None
    expiry_date: date
    purchase_price: float
    mrp: float
    selling_price: float
    quantity: int
    free_quantity: Optional[int] = 0
    supplier_id: Optional[int] = None
    status: Optional[str] = "AVAILABLE"

class BatchCreate(BatchBase):
    medicine_id: int

class BatchUpdate(BaseModel):
    purchase_price: Optional[float] = None
    mrp: Optional[float] = None
    selling_price: Optional[float] = None
    quantity: Optional[int] = None
    status: Optional[str] = None

class BatchResponse(BatchBase):
    id: int
    medicine_id: int
    is_expired: bool = False
    days_to_expiry: int = 0
    medicine_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class MedicineBase(BaseModel):
    name: str
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = "Allopathy"
    hsn_code: Optional[str] = "3004"
    gst_rate: float = 12.00
    rack_location: Optional[str] = None
    unit: Optional[str] = "Strip"
    min_stock_level: int = 10
    default_purchase_price: Optional[float] = 0.00
    default_selling_price: Optional[float] = 0.00
    barcode: Optional[str] = None
    is_prescription_required: bool = False
    is_active: bool = True

class MedicineCreate(MedicineBase):
    # Optional initial batch if registering stock directly
    initial_batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    quantity: Optional[int] = None
    supplier_id: Optional[int] = None

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    hsn_code: Optional[str] = None
    gst_rate: Optional[float] = None
    rack_location: Optional[str] = None
    unit: Optional[str] = None
    min_stock_level: Optional[int] = None
    default_purchase_price: Optional[float] = None
    default_selling_price: Optional[float] = None
    barcode: Optional[str] = None
    is_prescription_required: Optional[bool] = None
    is_active: Optional[bool] = None

class MedicineResponse(MedicineBase):
    id: int
    item_code: Optional[str] = None
    total_stock: int = 0
    batches: List[BatchResponse] = []
    model_config = ConfigDict(from_attributes=True)

# ----------------- Purchase Entry Schemas -----------------
class PurchaseItemInput(BaseModel):
    medicine_id: Optional[int] = None
    medicine_name: str
    batch_number: str
    manufacturing_date: Optional[date] = None
    expiry_date: date
    quantity: int
    free_quantity: Optional[int] = 0
    purchase_price: float
    mrp: float
    selling_price: float
    discount_percent: Optional[float] = 0.00
    gst_rate: float = 12.00

class PurchaseCreate(BaseModel):
    supplier_id: int
    supplier_invoice_number: str
    invoice_date: date
    received_date: date
    additional_charges: Optional[float] = 0.00
    paid_amount: Optional[float] = 0.00
    notes: Optional[str] = None
    items: List[PurchaseItemInput]

class PurchaseResponse(BaseModel):
    id: int
    purchase_number: str
    supplier_id: int
    supplier_name: Optional[str] = None
    supplier_invoice_number: str
    invoice_date: date
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    paid_amount: float
    balance_amount: float
    payment_status: str
    status: str
    bill_filename: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# ----------------- POS Billing Schemas -----------------
class SaleItemInput(BaseModel):
    medicine_id: int
    batch_id: int
    quantity: int
    unit_price: float
    discount_percent: Optional[float] = 0.00

class SaleCreate(BaseModel):
    customer_id: Optional[int] = None
    customer_name: Optional[str] = "Walk-in Customer"
    customer_mobile: Optional[str] = None
    doctor_name: Optional[str] = None
    payment_method: str = "CASH"  # CASH, UPI, CARD, CREDIT, MIXED
    paid_amount: Optional[float] = None
    items: List[SaleItemInput]

class SaleItemResponse(BaseModel):
    id: int
    medicine_name: str
    generic_name: Optional[str] = None
    batch_number: str
    expiry_date: date
    hsn_code: str
    quantity: int
    unit_price: float
    discount_percent: float
    discount_amount: float
    taxable_amount: float
    gst_rate: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_amount: float
    model_config = ConfigDict(from_attributes=True)

class SaleResponse(BaseModel):
    id: int
    invoice_number: str
    customer_id: Optional[int] = None
    customer_name: str
    customer_mobile: Optional[str] = None
    doctor_name: Optional[str] = None
    invoice_date: date
    invoice_time: time
    subtotal: float
    discount_amount: float
    taxable_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    tax_amount: float
    round_off: float
    net_amount: float
    paid_amount: float
    balance_amount: float
    payment_method: str
    payment_status: str
    status: str
    items: List[SaleItemResponse] = []
    model_config = ConfigDict(from_attributes=True)

# ----------------- Returns Schemas -----------------
class SalesReturnItemInput(BaseModel):
    sale_item_id: int
    quantity: int
    restock_status: str = "RESTOCKED"  # RESTOCKED or DAMAGED_EXPIRED

class SalesReturnCreate(BaseModel):
    sale_id: int
    reason: str
    refund_method: str = "CASH"
    items: List[SalesReturnItemInput]

class PurchaseReturnItemInput(BaseModel):
    medicine_id: int
    batch_id: int
    quantity: int

class PurchaseReturnCreate(BaseModel):
    supplier_id: int
    purchase_id: Optional[int] = None
    reason: str
    items: List[PurchaseReturnItemInput]

# ----------------- Expense Schemas -----------------
class ExpenseCreate(BaseModel):
    expense_category: str
    description: str
    amount: float
    expense_date: Optional[date] = None
    payment_method: str = "CASH"
    receipt_reference: Optional[str] = None

class ExpenseResponse(ExpenseCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- Alert & Dashboard Schemas -----------------
class ExpiryAlertItem(BaseModel):
    batch_id: int
    medicine_id: int
    medicine_name: str
    generic_name: Optional[str] = None
    rack_location: Optional[str] = None
    batch_number: str
    expiry_date: date
    quantity: int
    purchase_price: float
    stock_value: float
    days_remaining: int
    status_level: str  # ORANGE (expiring in 6 months) or RED (expired)

class LowStockAlertItem(BaseModel):
    medicine_id: int
    medicine_name: str
    generic_name: Optional[str] = None
    current_stock: int
    min_stock_level: int
    suggested_reorder_qty: int
    unit: str
    rack_location: Optional[str] = None
    estimated_reorder_cost: float

class DashboardStats(BaseModel):
    today_sales: float
    today_bills_count: int
    total_medicines: int
    total_available_stock: int
    registered_customers: int
    today_purchases: float
    low_stock_count: int
    near_expiry_count: int
    expired_count: int
    estimated_gross_profit_today: float
    monthly_sales_chart: dict
    recent_transactions: List[dict]
    recent_notifications: List[dict]
