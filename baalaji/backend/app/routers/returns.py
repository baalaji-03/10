from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import (
    Sale, SaleItem, SalesReturn, SalesReturnItem,
    PurchaseReturn, PurchaseReturnItem,
    MedicineBatch, StockMovement, Supplier, AuditLog
)
from backend.app.schemas import SalesReturnCreate, PurchaseReturnCreate
from backend.app.auth import require_roles

router = APIRouter(prefix="/api/returns", tags=["Returns & Refunds"])

@router.post("/sales")
def create_sales_return(
    ret_in: SalesReturnCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist"]))
):
    sale = db.query(Sale).filter(Sale.id == ret_in.sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale invoice not found")

    count = db.query(SalesReturn).count() + 1
    ret_number = f"SRET-{date.today().strftime('%Y%m')}-{count:04d}"

    tot_subtotal = 0.0
    tot_tax = 0.0
    tot_refund = 0.0

    return_items = []
    stock_restocks = []

    for itm in ret_in.items:
        s_item = db.query(SaleItem).filter(SaleItem.id == itm.sale_item_id, SaleItem.sale_id == sale.id).first()
        if not s_item:
            raise HTTPException(status_code=404, detail=f"Sale item ID {itm.sale_item_id} not found on this bill")

        if itm.quantity <= 0 or itm.quantity > s_item.quantity:
            raise HTTPException(status_code=400, detail=f"Return quantity {itm.quantity} is invalid for item {s_item.medicine_name}")

        unit_refund_rate = float(s_item.taxable_amount) / s_item.quantity
        item_tax_sum = float((s_item.cgst_amount or 0) + (s_item.sgst_amount or 0) + (s_item.igst_amount or 0))
        line_tax = (item_tax_sum / s_item.quantity) * itm.quantity
        line_total = (float(s_item.total_amount) / s_item.quantity) * itm.quantity

        tot_subtotal += (unit_refund_rate * itm.quantity)
        tot_tax += line_tax
        tot_refund += line_total

        # Handle batch restock if RESTOCKED
        batch = db.query(MedicineBatch).filter(MedicineBatch.id == s_item.batch_id).first()
        if batch and itm.restock_status == "RESTOCKED":
            prev_q = batch.quantity
            batch.quantity += itm.quantity
            new_q = batch.quantity
            if batch.status == "DEPLETED":
                batch.status = "AVAILABLE"
            stock_restocks.append((s_item.medicine_id, batch.id, itm.quantity, prev_q, new_q, s_item.medicine_name))

        sr_item = SalesReturnItem(
            sale_item_id=s_item.id,
            medicine_id=s_item.medicine_id,
            batch_id=s_item.batch_id,
            quantity=itm.quantity,
            refund_rate=unit_refund_rate,
            tax_amount=line_tax,
            total_amount=line_total,
            restock_status=itm.restock_status
        )
        return_items.append(sr_item)

    rounded_refund = round(tot_refund)

    s_ret = SalesReturn(
        return_number=ret_number,
        sale_id=sale.id,
        customer_id=sale.customer_id,
        return_date=date.today(),
        reason=ret_in.reason,
        subtotal=tot_subtotal,
        tax_amount=tot_tax,
        total_refund_amount=rounded_refund,
        refund_method=ret_in.refund_method,
        created_by_user_id=current_user.id
    )
    db.add(s_ret)
    db.flush()

    for r_item in return_items:
        r_item.sales_return_id = s_ret.id
        db.add(r_item)

    for m_id, b_id, q_ret, prev_q, new_q, m_name in stock_restocks:
        sm = StockMovement(
            medicine_id=m_id,
            batch_id=b_id,
            movement_type="SALE_RETURN",
            quantity_changed=q_ret,
            previous_quantity=prev_q,
            new_quantity=new_q,
            reference_type="SALES_RETURN",
            reference_id=s_ret.id,
            notes=f"Customer returned {q_ret}x {m_name} (Bill {sale.invoice_number})",
            user_id=current_user.id
        )
        db.add(sm)

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="SALES_RETURN",
        module="POS_BILLING",
        details=f"Processed return {ret_number} for sale {sale.invoice_number} (₹{rounded_refund:.2f})"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "return_number": ret_number,
        "total_refund_amount": rounded_refund
    }

@router.post("/purchases")
def create_purchase_return(
    ret_in: PurchaseReturnCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist", "Inventory Staff"]))
):
    supplier = db.query(Supplier).filter(Supplier.id == ret_in.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    count = db.query(PurchaseReturn).count() + 1
    ret_number = f"PRET-{date.today().strftime('%Y%m')}-{count:04d}"

    tot_subtotal = 0.0
    tot_tax = 0.0
    tot_refund = 0.0

    return_items = []
    stock_deductions = []

    for itm in ret_in.items:
        batch = db.query(MedicineBatch).filter(MedicineBatch.id == itm.batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail=f"Batch ID {itm.batch_id} not found")
        if batch.quantity < itm.quantity:
            raise HTTPException(status_code=400, detail=f"Cannot return {itm.quantity} units; only {batch.quantity} available in batch {batch.batch_number}")

        cost = float(batch.purchase_price) * itm.quantity
        gst_amt = cost * 0.12 # approx tax
        line_total = cost + gst_amt

        tot_subtotal += cost
        tot_tax += gst_amt
        tot_refund += line_total

        # Deduct from batch
        prev_q = batch.quantity
        batch.quantity -= itm.quantity
        new_q = batch.quantity
        if new_q == 0:
            batch.status = "DEPLETED"

        stock_deductions.append((batch.medicine_id, batch.id, itm.quantity, prev_q, new_q, batch.batch_number))

        pr_item = PurchaseReturnItem(
            medicine_id=batch.medicine_id,
            batch_id=batch.id,
            batch_number=batch.batch_number,
            quantity=itm.quantity,
            unit_cost=batch.purchase_price,
            tax_amount=gst_amt,
            total_amount=line_total
        )
        return_items.append(pr_item)

    rounded_refund = round(tot_refund)

    p_ret = PurchaseReturn(
        return_number=ret_number,
        purchase_id=ret_in.purchase_id,
        supplier_id=supplier.id,
        return_date=date.today(),
        reason=ret_in.reason,
        subtotal=tot_subtotal,
        tax_amount=tot_tax,
        total_refund_amount=rounded_refund,
        status="COMPLETED",
        created_by_user_id=current_user.id
    )
    db.add(p_ret)
    db.flush()

    for r_item in return_items:
        r_item.purchase_return_id = p_ret.id
        db.add(r_item)

    # Log stock movements
    for m_id, b_id, q_ded, prev_q, new_q, b_num in stock_deductions:
        sm = StockMovement(
            medicine_id=m_id,
            batch_id=b_id,
            movement_type="PURCHASE_RETURN",
            quantity_changed=-q_ded,
            previous_quantity=prev_q,
            new_quantity=new_q,
            reference_type="PURCHASE_RETURN",
            reference_id=p_ret.id,
            notes=f"Returned {q_ded} units of batch {b_num} to {supplier.name}",
            user_id=current_user.id
        )
        db.add(sm)

    # Reduce supplier balance or register credit
    current_bal = float(supplier.outstanding_balance or 0)
    supplier.outstanding_balance = max(0.0, current_bal - rounded_refund)

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="PURCHASE_RETURN",
        module="PURCHASE",
        details=f"Returned goods to {supplier.name} ({ret_number}) worth ₹{rounded_refund:.2f}"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "return_number": ret_number,
        "total_refund_amount": rounded_refund,
        "updated_supplier_balance": float(supplier.outstanding_balance)
    }
