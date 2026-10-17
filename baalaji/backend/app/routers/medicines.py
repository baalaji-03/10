from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.database import get_db
from backend.app.models import Medicine, MedicineBatch, StockMovement, AuditLog
from backend.app.schemas import (
    MedicineCreate, MedicineUpdate, MedicineResponse,
    BatchBase, BatchResponse
)
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/medicines", tags=["Medicines & Inventory"])

@router.get("", response_model=List[MedicineResponse])
def get_medicines(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Medicine).filter(Medicine.is_active == True)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Medicine.name.ilike(search_fmt),
                Medicine.generic_name.ilike(search_fmt),
                Medicine.item_code.ilike(search_fmt),
                Medicine.barcode.ilike(search_fmt),
                Medicine.manufacturer.ilike(search_fmt)
            )
        )
    if category:
        query = query.filter(Medicine.category == category)

    meds = query.order_by(Medicine.name).all()
    today = date.today()

    result = []
    for m in meds:
        batches_out = []
        tot_stock = 0
        for b in m.batches:
            days_rem = (b.expiry_date - today).days if b.expiry_date else 0
            is_exp = days_rem <= 0
            batches_out.append(BatchResponse(
                id=b.id,
                medicine_id=b.medicine_id,
                batch_number=b.batch_number,
                manufacturing_date=b.manufacturing_date,
                expiry_date=b.expiry_date,
                purchase_price=float(b.purchase_price or 0),
                mrp=float(b.mrp or 0),
                selling_price=float(b.selling_price or 0),
                quantity=b.quantity,
                free_quantity=b.free_quantity or 0,
                supplier_id=b.supplier_id,
                status=b.status,
                is_expired=is_exp,
                days_to_expiry=days_rem,
                medicine_name=m.name
            ))
            if not is_exp:
                tot_stock += b.quantity

        res = MedicineResponse.model_validate(m)
        res.total_stock = tot_stock
        res.batches = batches_out
        result.append(res)

    return result

@router.get("/barcode/{barcode}", response_model=MedicineResponse)
def lookup_by_barcode(
    barcode: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    med = db.query(Medicine).filter(
        (Medicine.barcode == barcode.strip()) | (Medicine.item_code == barcode.strip()),
        Medicine.is_active == True
    ).first()
    if not med:
        raise HTTPException(status_code=404, detail=f"No medicine found with barcode/code: {barcode}")
    
    today = date.today()
    batches_out = []
    tot_stock = 0
    for b in med.batches:
        days_rem = (b.expiry_date - today).days if b.expiry_date else 0
        is_exp = days_rem <= 0
        batches_out.append(BatchResponse(
            id=b.id,
            medicine_id=b.medicine_id,
            batch_number=b.batch_number,
            manufacturing_date=b.manufacturing_date,
            expiry_date=b.expiry_date,
            purchase_price=float(b.purchase_price or 0),
            mrp=float(b.mrp or 0),
            selling_price=float(b.selling_price or 0),
            quantity=b.quantity,
            free_quantity=b.free_quantity or 0,
            supplier_id=b.supplier_id,
            status=b.status,
            is_expired=is_exp,
            days_to_expiry=days_rem,
            medicine_name=med.name
        ))
        if not is_exp:
            tot_stock += b.quantity

    res = MedicineResponse.model_validate(med)
    res.total_stock = tot_stock
    res.batches = batches_out
    return res

@router.post("", response_model=MedicineResponse)
def create_medicine(
    med_in: MedicineCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist", "Inventory Staff"]))
):
    # Check duplicate
    existing = db.query(Medicine).filter(Medicine.name.ilike(med_in.name.strip())).first()
    if existing:
        raise HTTPException(status_code=400, detail="A medicine with this name already exists.")

    # Generate item code if not provided
    count = db.query(Medicine).count() + 1
    item_code = f"MED-{count:04d}"

    med = Medicine(
        item_code=item_code,
        barcode=med_in.barcode,
        name=med_in.name.strip(),
        generic_name=med_in.generic_name,
        manufacturer=med_in.manufacturer,
        category=med_in.category or "Allopathy",
        hsn_code=med_in.hsn_code or "3004",
        gst_rate=med_in.gst_rate,
        rack_location=med_in.rack_location,
        unit=med_in.unit or "Strip",
        min_stock_level=med_in.min_stock_level,
        default_purchase_price=med_in.default_purchase_price or 0.00,
        default_selling_price=med_in.default_selling_price or 0.00,
        is_prescription_required=med_in.is_prescription_required,
        is_active=True
    )
    db.add(med)
    db.flush()

    # Optional initial batch
    if med_in.initial_batch_number and med_in.expiry_date and med_in.quantity:
        status_val = "EXPIRED" if med_in.expiry_date <= date.today() else "AVAILABLE"
        batch = MedicineBatch(
            medicine_id=med.id,
            batch_number=med_in.initial_batch_number.strip(),
            expiry_date=med_in.expiry_date,
            purchase_price=med_in.default_purchase_price or 0.00,
            mrp=med_in.default_selling_price or 0.00,
            selling_price=med_in.default_selling_price or 0.00,
            quantity=med_in.quantity,
            supplier_id=med_in.supplier_id,
            status=status_val
        )
        db.add(batch)
        db.flush()

        movement = StockMovement(
            medicine_id=med.id,
            batch_id=batch.id,
            movement_type="PURCHASE",
            quantity_changed=med_in.quantity,
            previous_quantity=0,
            new_quantity=med_in.quantity,
            reference_type="INITIAL_ENTRY",
            notes="Opening stock entry",
            user_id=current_user.id
        )
        db.add(movement)

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE_MEDICINE",
        module="INVENTORY",
        details=f"Created medicine {med.name} (Code: {item_code})"
    )
    db.add(audit)
    db.commit()
    db.refresh(med)

    res = MedicineResponse.model_validate(med)
    res.total_stock = sum(b.quantity for b in med.batches if b.status != "EXPIRED")
    return res

@router.put("/{medicine_id}", response_model=MedicineResponse)
def update_medicine(
    medicine_id: int,
    med_in: MedicineUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist", "Inventory Staff"]))
):
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")

    for field, val in med_in.model_dump(exclude_unset=True).items():
        setattr(med, field, val)

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE_MEDICINE",
        module="INVENTORY",
        details=f"Updated medicine {med.name} (ID: {med.id})"
    )
    db.add(audit)
    db.commit()
    db.refresh(med)

    res = MedicineResponse.model_validate(med)
    res.total_stock = sum(b.quantity for b in med.batches if b.status != "EXPIRED")
    return res

@router.post("/{medicine_id}/batches", response_model=BatchResponse)
def add_batch(
    medicine_id: int,
    batch_in: BatchBase = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist", "Inventory Staff"]))
):
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")

    existing_batch = db.query(MedicineBatch).filter(
        MedicineBatch.medicine_id == medicine_id,
        MedicineBatch.batch_number == batch_in.batch_number.strip()
    ).first()

    today = date.today()
    status_val = "EXPIRED" if batch_in.expiry_date <= today else "AVAILABLE"

    if existing_batch:
        # Update existing batch quantity
        prev_q = existing_batch.quantity
        new_q = prev_q + batch_in.quantity
        existing_batch.quantity = new_q
        existing_batch.purchase_price = batch_in.purchase_price
        existing_batch.mrp = batch_in.mrp
        existing_batch.selling_price = batch_in.selling_price
        existing_batch.expiry_date = batch_in.expiry_date
        existing_batch.status = status_val
        batch = existing_batch
        q_change = batch_in.quantity
    else:
        batch = MedicineBatch(
            medicine_id=medicine_id,
            batch_number=batch_in.batch_number.strip(),
            manufacturing_date=batch_in.manufacturing_date,
            expiry_date=batch_in.expiry_date,
            purchase_price=batch_in.purchase_price,
            mrp=batch_in.mrp,
            selling_price=batch_in.selling_price,
            quantity=batch_in.quantity,
            free_quantity=batch_in.free_quantity or 0,
            supplier_id=batch_in.supplier_id,
            status=status_val
        )
        db.add(batch)
        db.flush()
        prev_q = 0
        new_q = batch_in.quantity
        q_change = batch_in.quantity

    movement = StockMovement(
        medicine_id=medicine_id,
        batch_id=batch.id,
        movement_type="PURCHASE",
        quantity_changed=q_change,
        previous_quantity=prev_q,
        new_quantity=new_q,
        reference_type="BATCH_ENTRY",
        notes=f"Batch {batch.batch_number} added/updated manually",
        user_id=current_user.id
    )
    db.add(movement)
    db.commit()
    db.refresh(batch)

    days_rem = (batch.expiry_date - today).days if batch.expiry_date else 0
    return BatchResponse(
        id=batch.id,
        medicine_id=batch.medicine_id,
        batch_number=batch.batch_number,
        manufacturing_date=batch.manufacturing_date,
        expiry_date=batch.expiry_date,
        purchase_price=float(batch.purchase_price),
        mrp=float(batch.mrp),
        selling_price=float(batch.selling_price),
        quantity=batch.quantity,
        free_quantity=batch.free_quantity or 0,
        supplier_id=batch.supplier_id,
        status=batch.status,
        is_expired=days_rem <= 0,
        days_to_expiry=days_rem,
        medicine_name=med.name
    )
