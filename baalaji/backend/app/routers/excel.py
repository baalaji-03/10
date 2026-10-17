from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Medicine, MedicineBatch, Sale, AuditLog
from backend.app.services.excel_service import (
    export_inventory_excel, export_batches_and_expiry_excel,
    export_sales_excel, export_gst_summary_excel,
    generate_medicine_template, generate_purchase_template,
    parse_and_validate_medicine_excel
)
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/excel", tags=["Excel Import & Export"])

# ----------------- Export Endpoints -----------------
@router.get("/export/inventory")
def export_inventory(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    medicines = db.query(Medicine).filter(Medicine.is_active == True).all()
    buf = export_inventory_excel(medicines)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Inventory_{date.today()}.xlsx"}
    )

@router.get("/export/batches")
def export_batches(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    batches = db.query(MedicineBatch).order_by(MedicineBatch.expiry_date.asc()).all()
    buf = export_batches_and_expiry_excel(batches)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Batches_and_Expiry_{date.today()}.xlsx"}
    )

@router.get("/export/sales")
def export_sales(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    sales = db.query(Sale).filter(Sale.status == "COMPLETED").order_by(Sale.id.desc()).all()
    buf = export_sales_excel(sales)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Sales_Report_{date.today()}.xlsx"}
    )

@router.get("/export/gst-summary")
def export_gst(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    sales = db.query(Sale).filter(Sale.status == "COMPLETED").order_by(Sale.id.desc()).all()
    buf = export_gst_summary_excel(sales)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=GSTR1_Summary_{date.today()}.xlsx"}
    )

# ----------------- Templates -----------------
@router.get("/template/medicines")
def get_med_template(current_user = Depends(get_current_user)):
    buf = generate_medicine_template()
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Medicine_Import_Template.xlsx"}
    )

@router.get("/template/purchases")
def get_pur_template(current_user = Depends(get_current_user)):
    buf = generate_purchase_template()
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Purchase_Import_Template.xlsx"}
    )

# ----------------- Upload Preview & Confirm -----------------
@router.post("/upload/medicines/preview")
async def preview_medicine_upload(
    file: UploadFile = File(...),
    current_user = Depends(require_roles(["Admin", "Pharmacist", "Inventory Staff"]))
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel (.xlsx) file.")

    content = await file.read()
    result = parse_and_validate_medicine_excel(content)
    return result

@router.post("/upload/medicines/confirm")
def confirm_medicine_upload(
    rows: list,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist", "Inventory Staff"]))
):
    """
    Persists validated rows into the database after user confirmation.
    Primary source of truth remains the database.
    """
    if not rows:
        raise HTTPException(status_code=400, detail="No rows provided for import.")

    added_count = 0
    updated_count = 0

    for item in rows:
        name = item.get("name")
        if not name:
            continue

        existing = db.query(Medicine).filter(Medicine.name.ilike(name.strip())).first()
        if existing:
            # Update fields
            if item.get("generic_name"):
                existing.generic_name = item.get("generic_name")
            if item.get("manufacturer"):
                existing.manufacturer = item.get("manufacturer")
            if item.get("category"):
                existing.category = item.get("category")
            if item.get("hsn_code"):
                existing.hsn_code = item.get("hsn_code")
            if item.get("gst_rate") is not None:
                existing.gst_rate = item.get("gst_rate")
            if item.get("min_stock_level") is not None:
                existing.min_stock_level = item.get("min_stock_level")
            if item.get("default_purchase_price") is not None:
                existing.default_purchase_price = item.get("default_purchase_price")
            if item.get("default_selling_price") is not None:
                existing.default_selling_price = item.get("default_selling_price")
            if item.get("barcode"):
                existing.barcode = item.get("barcode")
            updated_count += 1
        else:
            c = db.query(Medicine).count() + 1
            code = item.get("item_code") or f"MED-{c:04d}"
            new_med = Medicine(
                item_code=code,
                barcode=item.get("barcode"),
                name=name.strip(),
                generic_name=item.get("generic_name"),
                manufacturer=item.get("manufacturer"),
                category=item.get("category") or "Allopathy",
                hsn_code=item.get("hsn_code") or "3004",
                gst_rate=item.get("gst_rate") or 12.0,
                rack_location=item.get("rack_location"),
                unit=item.get("unit") or "Strip",
                min_stock_level=item.get("min_stock_level") or 10,
                default_purchase_price=item.get("default_purchase_price") or 0.0,
                default_selling_price=item.get("default_selling_price") or 0.0,
                is_active=True
            )
            db.add(new_med)
            added_count += 1

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="EXCEL_IMPORT_MEDICINES",
        module="INVENTORY",
        details=f"Imported {added_count} new medicines, updated {updated_count} medicines from Excel"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": f"Successfully processed {added_count + updated_count} medicines ({added_count} created, {updated_count} updated).",
        "added_count": added_count,
        "updated_count": updated_count
    }
