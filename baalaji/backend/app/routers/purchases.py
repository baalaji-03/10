from datetime import date
from pathlib import Path
import uuid
from typing import List, Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import (
    Purchase, PurchaseBill, PurchaseBillContent, PurchaseItem, Supplier, Medicine,
    MedicineBatch, StockMovement, AuditLog
)
from backend.app.schemas import PurchaseCreate, PurchaseResponse
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/purchases", tags=["Purchases & Suppliers"])
MAX_PURCHASE_BILL_SIZE = 4 * 1024 * 1024
PURCHASE_BILL_TYPES = {
    ".pdf": ("application/pdf", b"%PDF-"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
}

@router.get("", response_model=List[PurchaseResponse])
def get_purchases(
    supplier_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Purchase)
    if supplier_id:
        query = query.filter(Purchase.supplier_id == supplier_id)
    if start_date:
        query = query.filter(Purchase.invoice_date >= start_date)
    if end_date:
        query = query.filter(Purchase.invoice_date <= end_date)

    purchases = query.order_by(Purchase.id.desc()).all()
    result = []
    for p in purchases:
        res = PurchaseResponse(
            id=p.id,
            purchase_number=p.purchase_number,
            supplier_id=p.supplier_id,
            supplier_name=p.supplier.name if p.supplier else "Unknown",
            supplier_invoice_number=p.supplier_invoice_number,
            invoice_date=p.invoice_date,
            subtotal=float(p.subtotal or 0),
            discount_amount=float(p.discount_amount or 0),
            tax_amount=float(p.tax_amount or 0),
            total_amount=float(p.total_amount or 0),
            paid_amount=float(p.paid_amount or 0),
            balance_amount=float(p.balance_amount or 0),
            payment_status=p.payment_status,
            status=p.status,
            bill_filename=p.bill_attachment.original_filename if p.bill_attachment else None
        )
        result.append(res)
    return result

@router.get("/{purchase_id}")
def get_purchase_details(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase invoice not found")

    items_out = []
    for itm in purchase.items:
        items_out.append({
            "id": itm.id,
            "medicine_name": itm.medicine.name if itm.medicine else "Unknown",
            "batch_number": itm.batch_number,
            "expiry_date": itm.expiry_date.strftime("%d-%m-%Y") if itm.expiry_date else "",
            "quantity": itm.quantity,
            "free_quantity": itm.free_quantity,
            "purchase_price": float(itm.purchase_price),
            "mrp": float(itm.mrp),
            "selling_price": float(itm.selling_price),
            "discount_percent": float(itm.discount_percent or 0),
            "gst_rate": float(itm.gst_rate or 12),
            "total_amount": float(itm.total_amount)
        })

    return {
        "id": purchase.id,
        "purchase_number": purchase.purchase_number,
        "supplier_id": purchase.supplier_id,
        "supplier_name": purchase.supplier.name if purchase.supplier else "",
        "supplier_gstin": purchase.supplier.gstin if purchase.supplier else "",
        "supplier_invoice_number": purchase.supplier_invoice_number,
        "invoice_date": purchase.invoice_date.strftime("%d-%m-%Y") if purchase.invoice_date else "",
        "received_date": purchase.received_date.strftime("%d-%m-%Y") if purchase.received_date else "",
        "subtotal": float(purchase.subtotal or 0),
        "discount_amount": float(purchase.discount_amount or 0),
        "cgst_amount": float(purchase.cgst_amount or 0),
        "sgst_amount": float(purchase.sgst_amount or 0),
        "igst_amount": float(purchase.igst_amount or 0),
        "tax_amount": float(purchase.tax_amount or 0),
        "additional_charges": float(purchase.additional_charges or 0),
        "round_off": float(purchase.round_off or 0),
        "total_amount": float(purchase.total_amount or 0),
        "paid_amount": float(purchase.paid_amount or 0),
        "balance_amount": float(purchase.balance_amount or 0),
        "payment_status": purchase.payment_status,
        "bill_filename": purchase.bill_attachment.original_filename if purchase.bill_attachment else None,
        "notes": purchase.notes,
        "items": items_out
    }

@router.post("/{purchase_id}/bill")
async def upload_purchase_bill(
    purchase_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist", "Inventory Staff"]))
):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase invoice not found")

    original_filename = Path(file.filename or "").name
    extension = Path(original_filename).suffix.lower()
    file_type = PURCHASE_BILL_TYPES.get(extension)
    if not file_type:
        raise HTTPException(status_code=400, detail="Upload a supplier bill as a PDF, JPG, JPEG, or PNG file.")

    content = await file.read(MAX_PURCHASE_BILL_SIZE + 1)
    if len(content) > MAX_PURCHASE_BILL_SIZE:
        raise HTTPException(status_code=413, detail="Supplier bill files must be 4 MB or smaller.")
    content_type, signature = file_type
    if not content.startswith(signature):
        raise HTTPException(status_code=400, detail="The uploaded file does not match its file type.")

    previous_bill = purchase.bill_attachment
    if previous_bill:
        previous_bill.original_filename = original_filename
        previous_bill.stored_filename = f"{uuid.uuid4().hex}{extension}"
        previous_bill.content_type = content_type
        if previous_bill.file_content:
            previous_bill.file_content.content = content
        else:
            previous_bill.file_content = PurchaseBillContent(content=content)
    else:
        bill = PurchaseBill(
            purchase_id=purchase.id,
            original_filename=original_filename,
            stored_filename=f"{uuid.uuid4().hex}{extension}",
            content_type=content_type
        )
        bill.file_content = PurchaseBillContent(content=content)
        db.add(bill)
    db.commit()

    return {"message": "Supplier bill uploaded successfully.", "filename": original_filename}

@router.get("/{purchase_id}/bill")
def download_purchase_bill(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase invoice not found")
    bill = purchase.bill_attachment
    if not bill:
        raise HTTPException(status_code=404, detail="No supplier bill is attached to this purchase")

    if not bill.file_content:
        raise HTTPException(status_code=404, detail="The attached supplier bill file is missing")
    return Response(
        content=bill.file_content.content,
        media_type=bill.content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(bill.original_filename, safe='')}"
        }
    )

@router.post("", response_model=PurchaseResponse)
def create_purchase(
    purchase_in: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist", "Inventory Staff"]))
):
    # 1. Validate Supplier
    supplier = db.query(Supplier).filter(Supplier.id == purchase_in.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Selected supplier not found")

    # 2. Check Duplicate Supplier Invoice Number
    dup = db.query(Purchase).filter(
        Purchase.supplier_id == purchase_in.supplier_id,
        Purchase.supplier_invoice_number == purchase_in.supplier_invoice_number.strip()
    ).first()
    if dup:
        raise HTTPException(
            status_code=400,
            detail=f"Duplicate invoice! Invoice '{purchase_in.supplier_invoice_number}' already exists for supplier '{supplier.name}'."
        )

    if not purchase_in.items or len(purchase_in.items) == 0:
        raise HTTPException(status_code=400, detail="Purchase invoice must have at least one medicine item.")

    # 3. Generate unique purchase number (PUR-YYYYMM-XXXX)
    today = date.today()
    prefix = f"PUR-{today.strftime('%Y%m')}"
    p_count = db.query(Purchase).filter(Purchase.purchase_number.like(f"{prefix}%")).count() + 1
    purchase_number = f"{prefix}-{p_count:04d}"

    # 4. Calculate items, taxes, totals
    total_subtotal = 0.0
    total_discount = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    total_igst = 0.0
    total_tax = 0.0
    total_final = 0.0

    purchase_items = []
    stock_updates = []

    for itm in purchase_in.items:
        # Find or create medicine
        med = None
        if itm.medicine_id:
            med = db.query(Medicine).filter(Medicine.id == itm.medicine_id).first()
        if not med:
            med = db.query(Medicine).filter(Medicine.name.ilike(itm.medicine_name.strip())).first()
        if not med:
            # Auto-register new medicine from purchase entry
            count_m = db.query(Medicine).count() + 1
            med = Medicine(
                item_code=f"MED-{count_m:04d}",
                name=itm.medicine_name.strip(),
                hsn_code="3004",
                gst_rate=itm.gst_rate,
                min_stock_level=10,
                default_purchase_price=itm.purchase_price,
                default_selling_price=itm.selling_price,
                is_active=True
            )
            db.add(med)
            db.flush()

        gross = float(itm.purchase_price) * itm.quantity
        disc = gross * (float(itm.discount_percent or 0) / 100.0)
        taxable = gross - disc
        
        # Intra-state GST (CGST + SGST)
        rate = float(itm.gst_rate or 12.0)
        cgst_r = rate / 2.0
        sgst_r = rate / 2.0
        cgst_amt = taxable * (cgst_r / 100.0)
        sgst_amt = taxable * (sgst_r / 100.0)
        item_tax = cgst_amt + sgst_amt
        item_total = taxable + item_tax

        total_subtotal += gross
        total_discount += disc
        total_cgst += cgst_amt
        total_sgst += sgst_amt
        total_tax += item_tax
        total_final += item_total

        # Manage batch: find existing or create new
        batch = db.query(MedicineBatch).filter(
            MedicineBatch.medicine_id == med.id,
            MedicineBatch.batch_number == itm.batch_number.strip()
        ).first()

        prev_qty = 0
        total_qty_to_add = itm.quantity + (itm.free_quantity or 0)
        today_date = date.today()
        b_status = "EXPIRED" if itm.expiry_date <= today_date else "AVAILABLE"

        if batch:
            prev_qty = batch.quantity
            batch.quantity += total_qty_to_add
            batch.free_quantity = (batch.free_quantity or 0) + (itm.free_quantity or 0)
            batch.purchase_price = itm.purchase_price
            batch.mrp = itm.mrp
            batch.selling_price = itm.selling_price
            batch.expiry_date = itm.expiry_date
            batch.status = b_status
        else:
            batch = MedicineBatch(
                medicine_id=med.id,
                batch_number=itm.batch_number.strip(),
                manufacturing_date=itm.manufacturing_date,
                expiry_date=itm.expiry_date,
                purchase_price=itm.purchase_price,
                mrp=itm.mrp,
                selling_price=itm.selling_price,
                quantity=total_qty_to_add,
                free_quantity=itm.free_quantity or 0,
                supplier_id=supplier.id,
                status=b_status
            )
            db.add(batch)
            db.flush()

        stock_updates.append((med.id, batch.id, total_qty_to_add, prev_qty, prev_qty + total_qty_to_add))

        p_item = PurchaseItem(
            medicine_id=med.id,
            batch_id=batch.id,
            batch_number=itm.batch_number.strip(),
            manufacturing_date=itm.manufacturing_date,
            expiry_date=itm.expiry_date,
            quantity=itm.quantity,
            free_quantity=itm.free_quantity or 0,
            purchase_price=itm.purchase_price,
            mrp=itm.mrp,
            selling_price=itm.selling_price,
            discount_percent=itm.discount_percent or 0.0,
            discount_amount=disc,
            gst_rate=itm.gst_rate,
            cgst_rate=cgst_r,
            sgst_rate=sgst_r,
            igst_rate=0.0,
            cgst_amount=cgst_amt,
            sgst_amount=sgst_amt,
            igst_amount=0.0,
            total_amount=item_total
        )
        purchase_items.append(p_item)

    # Add extra charges & round off
    grand_total = total_final + float(purchase_in.additional_charges or 0.0)
    rounded_grand_total = round(grand_total)
    round_off = rounded_grand_total - grand_total
    paid_amt = float(purchase_in.paid_amount or 0.0)
    bal_amt = rounded_grand_total - paid_amt

    pay_status = "PAID" if bal_amt <= 0.0 else ("PARTIAL" if paid_amt > 0 else "PENDING")

    # Create Purchase Master
    purchase = Purchase(
        purchase_number=purchase_number,
        supplier_id=supplier.id,
        supplier_invoice_number=purchase_in.supplier_invoice_number.strip(),
        invoice_date=purchase_in.invoice_date,
        received_date=purchase_in.received_date,
        subtotal=total_subtotal,
        discount_amount=total_discount,
        cgst_amount=total_cgst,
        sgst_amount=total_sgst,
        igst_amount=total_igst,
        tax_amount=total_tax,
        additional_charges=purchase_in.additional_charges or 0.0,
        round_off=round_off,
        total_amount=rounded_grand_total,
        paid_amount=paid_amt,
        balance_amount=bal_amt,
        payment_status=pay_status,
        status="CONFIRMED",
        notes=purchase_in.notes,
        created_by_user_id=current_user.id
    )
    db.add(purchase)
    db.flush()

    for itm in purchase_items:
        itm.purchase_id = purchase.id
        db.add(itm)

    # Log Stock Movements
    for m_id, b_id, q_added, prev_q, new_q in stock_updates:
        sm = StockMovement(
            medicine_id=m_id,
            batch_id=b_id,
            movement_type="PURCHASE",
            quantity_changed=q_added,
            previous_quantity=prev_q,
            new_quantity=new_q,
            reference_type="PURCHASE_INVOICE",
            reference_id=purchase.id,
            notes=f"Purchased from {supplier.name} (Inv: {purchase.supplier_invoice_number})",
            user_id=current_user.id
        )
        db.add(sm)

    # Update Supplier Outstanding Balance
    if bal_amt > 0:
        supplier.outstanding_balance = float(supplier.outstanding_balance or 0) + bal_amt

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE_PURCHASE",
        module="PURCHASE",
        details=f"Created purchase invoice {purchase_number} from {supplier.name} for ₹{rounded_grand_total:.2f}"
    )
    db.add(audit)
    db.commit()
    db.refresh(purchase)

    return PurchaseResponse(
        id=purchase.id,
        purchase_number=purchase.purchase_number,
        supplier_id=purchase.supplier_id,
        supplier_name=supplier.name,
        supplier_invoice_number=purchase.supplier_invoice_number,
        invoice_date=purchase.invoice_date,
        subtotal=float(purchase.subtotal),
        discount_amount=float(purchase.discount_amount),
        tax_amount=float(purchase.tax_amount),
        total_amount=float(purchase.total_amount),
        paid_amount=float(purchase.paid_amount),
        balance_amount=float(purchase.balance_amount),
        payment_status=purchase.payment_status,
        status=purchase.status
    )
