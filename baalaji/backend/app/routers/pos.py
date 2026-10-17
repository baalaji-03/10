from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.database import get_db
from backend.app.models import (
    Sale, SaleItem, Payment, MedicineBatch, Customer,
    StockMovement, PharmacySetting, AuditLog
)
from backend.app.schemas import (
    SaleCreate, SaleResponse
)
from backend.app.auth import get_current_user

router = APIRouter(prefix="/api/pos", tags=["GST Billing & POS"])

@router.get("/invoices")
def get_recent_invoices(
    search: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Sale)
    if search:
        s_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Sale.invoice_number.ilike(s_fmt),
                Sale.customer_name.ilike(s_fmt),
                Sale.customer_mobile.ilike(s_fmt)
            )
        )
    if start_date:
        query = query.filter(Sale.invoice_date >= start_date)
    if end_date:
        query = query.filter(Sale.invoice_date <= end_date)

    sales = query.order_by(Sale.id.desc()).limit(limit).all()
    out = []
    for s in sales:
        out.append({
            "id": s.id,
            "invoice_number": s.invoice_number,
            "invoice_date": s.invoice_date.strftime("%d-%m-%Y") if s.invoice_date else "",
            "invoice_time": s.invoice_time.strftime("%I:%M %p") if s.invoice_time else "",
            "customer_name": s.customer_name or "Walk-in Customer",
            "customer_mobile": s.customer_mobile or "",
            "doctor_name": s.doctor_name or "",
            "net_amount": float(s.net_amount or 0),
            "tax_amount": float(s.tax_amount or 0),
            "payment_method": s.payment_method,
            "payment_status": s.payment_status,
            "status": s.status,
            "items_count": len(s.items)
        })
    return out

@router.get("/invoices/{sale_id}", response_model=SaleResponse)
def get_invoice_by_id(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return sale

@router.post("/sale", response_model=SaleResponse)
def create_sale_transaction(
    sale_in: SaleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Atomic Point of Sale billing transaction.
    - Validates stock and strictly rejects expired medicine batches.
    - Atomically deducts stock from batch.
    - Records stock movement audit.
    - Calculates GST (CGST/SGST/IGST), COGS, and gross profit.
    """
    if not sale_in.items or len(sale_in.items) == 0:
        raise HTTPException(status_code=400, detail="Cannot generate bill with 0 items.")

    today = date.today()
    now_time = datetime.now().time()

    # Get pharmacy settings for prefix
    setting = db.query(PharmacySetting).first()
    p_prefix = setting.invoice_prefix if setting and setting.invoice_prefix else "INV"
    prefix = f"{p_prefix}-{today.strftime('%Y%m')}"
    s_count = db.query(Sale).filter(Sale.invoice_number.like(f"{prefix}%")).count() + 1
    invoice_number = f"{prefix}-{s_count:04d}"

    # Handle Customer (link or auto-create)
    cust_id = sale_in.customer_id
    cust_name = sale_in.customer_name or "Walk-in Customer"
    cust_mobile = sale_in.customer_mobile

    if cust_mobile and not cust_id:
        existing_cust = db.query(Customer).filter(Customer.mobile == cust_mobile.strip()).first()
        if existing_cust:
            cust_id = existing_cust.id
            cust_name = existing_cust.name
        else:
            # Quick register customer
            c_code = f"CUST-{db.query(Customer).count() + 1:04d}"
            new_cust = Customer(
                customer_code=c_code,
                name=cust_name,
                mobile=cust_mobile.strip()
            )
            db.add(new_cust)
            db.flush()
            cust_id = new_cust.id

    # Begin Atomic Item Processing
    total_subtotal = 0.0
    total_discount = 0.0
    total_taxable = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    total_igst = 0.0
    total_tax = 0.0
    total_final = 0.0
    total_cogs = 0.0
    total_gross_profit = 0.0

    sale_items = []
    stock_deductions = []

    for itm in sale_in.items:
        batch = db.query(MedicineBatch).filter(MedicineBatch.id == itm.batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail=f"Batch ID {itm.batch_id} not found.")

        med = batch.medicine
        if not med:
            raise HTTPException(status_code=404, detail=f"Medicine not found for batch {batch.batch_number}")

        # STRICT SAFETY CHECK 1: Expired Batches MUST NEVER BE SOLD
        if batch.expiry_date <= today or batch.status == "EXPIRED":
            raise HTTPException(
                status_code=400,
                detail=f"CRITICAL SAFETY VIOLATION: Batch '{batch.batch_number}' of '{med.name}' expired on {batch.expiry_date.strftime('%d-%m-%Y')} and CANNOT be dispensed!"
            )

        # STRICT SAFETY CHECK 2: Sufficient Stock Check
        if itm.quantity <= 0:
            raise HTTPException(status_code=400, detail="Item quantity must be greater than 0.")
        if batch.quantity < itm.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{med.name}' (Batch: {batch.batch_number}). Available: {batch.quantity}, Requested: {itm.quantity}."
            )

        # Financial & Tax Calculations
        gross_item = float(itm.unit_price) * itm.quantity
        disc_amt = gross_item * (float(itm.discount_percent or 0.0) / 100.0)
        taxable_amt = gross_item - disc_amt
        
        # Indian GST: CGST + SGST (50% each of total rate)
        rate = float(med.gst_rate or 12.0)
        cgst_r = rate / 2.0
        sgst_r = rate / 2.0
        cgst_amt = taxable_amt * (cgst_r / 100.0)
        sgst_amt = taxable_amt * (sgst_r / 100.0)
        itm_tax = cgst_amt + sgst_amt
        line_total = taxable_amt + itm_tax

        # Cost of Goods Sold & Profit
        cost_unit = float(batch.purchase_price or 0.0)
        cost_line = cost_unit * itm.quantity
        profit_line = taxable_amt - cost_line

        total_subtotal += gross_item
        total_discount += disc_amt
        total_taxable += taxable_amt
        total_cgst += cgst_amt
        total_sgst += sgst_amt
        total_tax += itm_tax
        total_final += line_total
        total_cogs += cost_line
        total_gross_profit += profit_line

        # Prepare Batch Stock Deduction
        prev_qty = batch.quantity
        new_qty = prev_qty - itm.quantity
        batch.quantity = new_qty
        if new_qty == 0:
            batch.status = "DEPLETED"
        elif new_qty <= med.min_stock_level:
            batch.status = "LOW_STOCK"

        stock_deductions.append((med.id, batch.id, itm.quantity, prev_qty, new_qty, batch.batch_number, med.name))

        s_item = SaleItem(
            medicine_id=med.id,
            batch_id=batch.id,
            medicine_name=med.name,
            generic_name=med.generic_name,
            batch_number=batch.batch_number,
            expiry_date=batch.expiry_date,
            hsn_code=med.hsn_code or "3004",
            quantity=itm.quantity,
            unit_price=itm.unit_price,
            purchase_price=batch.purchase_price,
            mrp=batch.mrp,
            discount_percent=itm.discount_percent or 0.0,
            discount_amount=disc_amt,
            taxable_amount=taxable_amt,
            gst_rate=rate,
            cgst_rate=cgst_r,
            sgst_rate=sgst_r,
            igst_rate=0.0,
            cgst_amount=cgst_amt,
            sgst_amount=sgst_amt,
            igst_amount=0.0,
            total_amount=line_total,
            cost_amount=cost_line,
            profit_amount=profit_line
        )
        sale_items.append(s_item)

    # Round Off Grand Total
    rounded_net = round(total_final)
    round_off = rounded_net - total_final
    paid_amt = float(sale_in.paid_amount if sale_in.paid_amount is not None else rounded_net)
    bal_amt = max(0.0, rounded_net - paid_amt)
    pay_status = "PAID" if bal_amt <= 0.0 else ("PARTIAL" if paid_amt > 0 else "CREDIT")

    # Create Master Sale Record
    sale = Sale(
        invoice_number=invoice_number,
        customer_id=cust_id,
        customer_name=cust_name,
        customer_mobile=cust_mobile,
        doctor_name=sale_in.doctor_name,
        invoice_date=today,
        invoice_time=now_time,
        subtotal=total_subtotal,
        discount_amount=total_discount,
        taxable_amount=total_taxable,
        cgst_amount=total_cgst,
        sgst_amount=total_sgst,
        igst_amount=total_igst,
        tax_amount=total_tax,
        round_off=round_off,
        net_amount=rounded_net,
        paid_amount=paid_amt,
        balance_amount=bal_amt,
        payment_method=sale_in.payment_method,
        payment_status=pay_status,
        status="COMPLETED",
        total_cost_of_goods=total_cogs,
        gross_profit=total_gross_profit,
        user_id=current_user.id
    )
    db.add(sale)
    db.flush()

    for item in sale_items:
        item.sale_id = sale.id
        db.add(item)

    # Record Payment Receipt
    if paid_amt > 0:
        pay = Payment(
            sale_id=sale.id,
            payment_method=sale_in.payment_method,
            amount=paid_amt,
            transaction_ref=f"TXN-{sale.invoice_number}",
            user_id=current_user.id
        )
        db.add(pay)

    # Record Stock Movements
    for m_id, b_id, q_deducted, prev_q, new_q, b_num, m_name in stock_deductions:
        sm = StockMovement(
            medicine_id=m_id,
            batch_id=b_id,
            movement_type="SALE",
            quantity_changed=-q_deducted,
            previous_quantity=prev_q,
            new_quantity=new_q,
            reference_type="SALE_INVOICE",
            reference_id=sale.id,
            notes=f"Sold {q_deducted} units of {m_name} (Batch: {b_num}) on Bill {sale.invoice_number}",
            user_id=current_user.id
        )
        db.add(sm)

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE_SALE",
        module="POS_BILLING",
        details=f"Completed sale {sale.invoice_number} for customer {cust_name} (₹{rounded_net:.2f})"
    )
    db.add(audit)
    db.commit()
    db.refresh(sale)

    return sale
