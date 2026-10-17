from datetime import date, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Medicine, MedicineBatch, PharmacySetting
from backend.app.schemas import ExpiryAlertItem, LowStockAlertItem
from backend.app.auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["Alerts & Notifications"])

@router.get("/expiry", response_model=List[ExpiryAlertItem])
def get_expiry_alerts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Identifies batches expiring within next 6 calendar months (ORANGE) and Expired (RED).
    """
    today = date.today()
    setting = db.query(PharmacySetting).first()
    warning_months = setting.expiry_warning_months if setting else 6
    six_months_ahead = today + timedelta(days=warning_months * 30)

    batches = db.query(MedicineBatch).filter(
        MedicineBatch.expiry_date <= six_months_ahead,
        MedicineBatch.quantity > 0
    ).order_by(MedicineBatch.expiry_date.asc()).all()

    alerts = []
    for b in batches:
        days_rem = (b.expiry_date - today).days if b.expiry_date else 0
        stock_val = float(b.purchase_price or 0.0) * b.quantity
        status_lvl = "RED" if days_rem <= 0 else "ORANGE"

        # Update batch status if expired
        if days_rem <= 0 and b.status != "EXPIRED":
            b.status = "EXPIRED"
            db.commit()

        alerts.append(ExpiryAlertItem(
            batch_id=b.id,
            medicine_id=b.medicine_id,
            medicine_name=b.medicine.name if b.medicine else "Unknown",
            generic_name=b.medicine.generic_name if b.medicine else None,
            rack_location=b.medicine.rack_location if b.medicine else None,
            batch_number=b.batch_number,
            expiry_date=b.expiry_date,
            quantity=b.quantity,
            purchase_price=float(b.purchase_price or 0.0),
            stock_value=stock_val,
            days_remaining=days_rem,
            status_level=status_lvl
        ))

    return alerts

@router.get("/low-stock", response_model=List[LowStockAlertItem])
def get_low_stock_alerts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Calculates available stock across active batches and identifies medicines below min_stock_level.
    Suggests reorder quantity and estimated cost.
    """
    setting = db.query(PharmacySetting).first()
    reorder_mult = float(setting.default_reorder_multiplier) if setting else 2.0

    medicines = db.query(Medicine).filter(Medicine.is_active == True).all()
    alerts = []

    for med in medicines:
        curr_stock = sum(b.quantity for b in med.batches if b.status != "EXPIRED")
        if curr_stock <= med.min_stock_level:
            target_stock = int(med.min_stock_level * reorder_mult)
            suggested_reorder = max(1, target_stock - curr_stock)
            cost = suggested_reorder * float(med.default_purchase_price or 0.0)

            alerts.append(LowStockAlertItem(
                medicine_id=med.id,
                medicine_name=med.name,
                generic_name=med.generic_name,
                current_stock=curr_stock,
                min_stock_level=med.min_stock_level,
                suggested_reorder_qty=suggested_reorder,
                unit=med.unit or "Strip",
                rack_location=med.rack_location,
                estimated_reorder_cost=cost
            ))

    return sorted(alerts, key=lambda x: x.current_stock)
