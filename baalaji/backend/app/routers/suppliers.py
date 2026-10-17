from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.database import get_db
from backend.app.models import Supplier, SupplierPayment, Purchase, AuditLog
from backend.app.schemas import (
    SupplierCreate, SupplierUpdate, SupplierResponse, SupplierPaymentCreate
)
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])

@router.get("", response_model=List[SupplierResponse])
def get_suppliers(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Supplier)
    if search:
        s_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Supplier.name.ilike(s_fmt),
                Supplier.phone.ilike(s_fmt),
                Supplier.gstin.ilike(s_fmt),
                Supplier.supplier_code.ilike(s_fmt)
            )
        )
    return query.order_by(Supplier.name).all()

@router.get("/{supplier_id}/ledger")
def get_supplier_ledger(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    purchases = db.query(Purchase).filter(Purchase.supplier_id == supplier_id).order_by(Purchase.invoice_date.desc()).all()
    payments = db.query(SupplierPayment).filter(SupplierPayment.supplier_id == supplier_id).order_by(SupplierPayment.payment_date.desc()).all()

    p_list = [
        {
            "id": p.id,
            "purchase_number": p.purchase_number,
            "supplier_invoice_number": p.supplier_invoice_number,
            "invoice_date": p.invoice_date.strftime("%d-%m-%Y") if p.invoice_date else "",
            "total_amount": float(p.total_amount or 0),
            "paid_amount": float(p.paid_amount or 0),
            "balance_amount": float(p.balance_amount or 0),
            "payment_status": p.payment_status
        }
        for p in purchases
    ]

    pay_list = [
        {
            "id": pay.id,
            "payment_number": pay.payment_number,
            "payment_date": pay.payment_date.strftime("%d-%m-%Y") if pay.payment_date else "",
            "amount": float(pay.amount or 0),
            "payment_method": pay.payment_method,
            "reference_number": pay.reference_number,
            "notes": pay.notes
        }
        for pay in payments
    ]

    return {
        "supplier": {
            "id": supplier.id,
            "name": supplier.name,
            "phone": supplier.phone,
            "gstin": supplier.gstin,
            "outstanding_balance": float(supplier.outstanding_balance or 0)
        },
        "purchases": p_list,
        "payments": pay_list
    }

@router.post("", response_model=SupplierResponse)
def create_supplier(
    sup_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist", "Inventory Staff"]))
):
    code_num = db.query(Supplier).count() + 1
    s_code = f"SUP-{code_num:03d}"

    sup = Supplier(
        supplier_code=s_code,
        name=sup_in.name.strip(),
        contact_person=sup_in.contact_person,
        phone=sup_in.phone.strip(),
        email=sup_in.email,
        gstin=sup_in.gstin,
        address=sup_in.address,
        city=sup_in.city,
        state=sup_in.state,
        state_code=sup_in.state_code or "33",
        dl_number=sup_in.dl_number,
        pan_number=sup_in.pan_number,
        outstanding_balance=sup_in.opening_balance or 0.00,
        is_active=True
    )
    db.add(sup)
    db.commit()
    db.refresh(sup)
    return sup

@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    sup_in: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist", "Inventory Staff"]))
):
    sup = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not sup:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for field, val in sup_in.model_dump(exclude_unset=True).items():
        setattr(sup, field, val)

    db.commit()
    db.refresh(sup)
    return sup

@router.post("/payments")
def record_supplier_payment(
    pay_in: SupplierPaymentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist", "Inventory Staff"]))
):
    supplier = db.query(Supplier).filter(Supplier.id == pay_in.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    count = db.query(SupplierPayment).count() + 1
    p_num = f"SPAY-{count:04d}"

    payment = SupplierPayment(
        payment_number=p_num,
        supplier_id=supplier.id,
        purchase_id=pay_in.purchase_id,
        payment_date=pay_in.payment_date or date.today(),
        amount=pay_in.amount,
        payment_method=pay_in.payment_method,
        reference_number=pay_in.reference_number,
        notes=pay_in.notes,
        created_by_user_id=current_user.id
    )
    db.add(payment)

    # Deduct from supplier balance
    current_bal = float(supplier.outstanding_balance or 0)
    supplier.outstanding_balance = max(0.0, current_bal - pay_in.amount)

    # If linked to specific purchase invoice, update purchase paid & balance amount
    if pay_in.purchase_id:
        p = db.query(Purchase).filter(Purchase.id == pay_in.purchase_id).first()
        if p:
            new_p_paid = float(p.paid_amount or 0) + pay_in.amount
            p.paid_amount = new_p_paid
            p.balance_amount = max(0.0, float(p.total_amount) - new_p_paid)
            if p.balance_amount == 0:
                p.payment_status = "PAID"
            elif new_p_paid > 0:
                p.payment_status = "PARTIAL"

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="SUPPLIER_PAYMENT",
        module="SUPPLIERS",
        details=f"Paid ₹{pay_in.amount:.2f} to {supplier.name} ({p_num})"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "payment_number": p_num,
        "remaining_supplier_balance": float(supplier.outstanding_balance)
    }
