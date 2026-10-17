from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models import (
    Sale, Purchase, Customer, Medicine, MedicineBatch, NotificationLog, PharmacySetting
)
from backend.app.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    today = date.today()
    setting = db.query(PharmacySetting).first()
    warning_months = setting.expiry_warning_months if setting else 6
    six_months_ahead = today + timedelta(days=warning_months * 30)

    # 1. Today's sales & bill count
    today_sales_query = db.query(
        func.coalesce(func.sum(Sale.net_amount), 0).label("total_sales"),
        func.coalesce(func.sum(Sale.gross_profit), 0).label("gross_profit"),
        func.count(Sale.id).label("bill_count")
    ).filter(Sale.invoice_date == today, Sale.status == "COMPLETED").first()

    today_sales = float(today_sales_query.total_sales or 0)
    today_profit = float(today_sales_query.gross_profit or 0)
    today_bills = int(today_sales_query.bill_count or 0)

    # 2. Total medicines and available stock
    total_meds = db.query(Medicine).filter(Medicine.is_active == True).count()
    total_stock = db.query(func.coalesce(func.sum(MedicineBatch.quantity), 0)).filter(
        MedicineBatch.status != "EXPIRED"
    ).scalar() or 0

    # 3. Registered customers
    registered_custs = db.query(Customer).count()

    # 4. Today's purchases
    today_purchases = db.query(func.coalesce(func.sum(Purchase.total_amount), 0)).filter(
        Purchase.invoice_date == today, Purchase.status == "CONFIRMED"
    ).scalar() or 0
    today_purchases = float(today_purchases)

    # 5. Low-stock count (medicines where sum of batch quantity <= min_stock_level)
    medicines = db.query(Medicine).filter(Medicine.is_active == True).all()
    low_stock_count = 0
    for med in medicines:
        curr_stock = sum(b.quantity for b in med.batches if b.status != "EXPIRED")
        if curr_stock <= med.min_stock_level:
            low_stock_count += 1

    # 6. Expiry alerts: Near expiry (<= 6 months and not expired) & Expired (<= today)
    expired_count = db.query(MedicineBatch).filter(
        MedicineBatch.expiry_date <= today,
        MedicineBatch.quantity > 0
    ).count()

    near_expiry_count = db.query(MedicineBatch).filter(
        MedicineBatch.expiry_date > today,
        MedicineBatch.expiry_date <= six_months_ahead,
        MedicineBatch.quantity > 0
    ).count()

    # 7. Monthly Sales & Purchase Chart Data (Last 6 months)
    chart_labels = []
    sales_trend = []
    purchase_trend = []

    for i in range(5, -1, -1):
        # Calculate month
        first_of_month = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        next_month = (first_of_month + timedelta(days=32)).replace(day=1)
        
        m_label = first_of_month.strftime("%b %Y")
        chart_labels.append(m_label)

        m_sales = db.query(func.coalesce(func.sum(Sale.net_amount), 0)).filter(
            Sale.invoice_date >= first_of_month,
            Sale.invoice_date < next_month,
            Sale.status == "COMPLETED"
        ).scalar() or 0
        sales_trend.append(float(m_sales))

        m_purchase = db.query(func.coalesce(func.sum(Purchase.total_amount), 0)).filter(
            Purchase.invoice_date >= first_of_month,
            Purchase.invoice_date < next_month,
            Purchase.status == "CONFIRMED"
        ).scalar() or 0
        purchase_trend.append(float(m_purchase))

    # 8. Recent 5 sales transactions
    recent_sales = db.query(Sale).order_by(Sale.id.desc()).limit(5).all()
    recent_txs = [
        {
            "id": s.id,
            "invoice_number": s.invoice_number,
            "customer_name": s.customer_name or "Walk-in",
            "date": s.invoice_date.strftime("%d-%m-%Y") if s.invoice_date else "",
            "amount": float(s.net_amount or 0),
            "payment_method": s.payment_method,
            "status": s.status
        }
        for s in recent_sales
    ]

    # 9. Recent notifications
    recent_notifs = db.query(NotificationLog).order_by(NotificationLog.id.desc()).limit(5).all()
    notif_list = [
        {
            "id": n.id,
            "type": n.notification_type,
            "subject": n.subject,
            "status": n.status,
            "sent_at": n.sent_at.strftime("%d-%m-%Y %H:%M") if n.sent_at else ""
        }
        for n in recent_notifs
    ]

    return {
        "today_sales": today_sales,
        "today_bills_count": today_bills,
        "total_medicines": total_meds,
        "total_available_stock": total_stock,
        "registered_customers": registered_custs,
        "today_purchases": today_purchases,
        "low_stock_count": low_stock_count,
        "near_expiry_count": near_expiry_count,
        "expired_count": expired_count,
        "estimated_gross_profit_today": today_profit,
        "monthly_chart": {
            "labels": chart_labels,
            "sales": sales_trend,
            "purchases": purchase_trend
        },
        "recent_transactions": recent_txs,
        "recent_notifications": notif_list
    }
