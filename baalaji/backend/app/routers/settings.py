from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import PharmacySetting, AuditLog, NotificationLog, Medicine, MedicineBatch, Sale
from backend.app.schemas import PharmacySettingUpdate, PharmacySettingResponse, SmtpTestRequest
from backend.app.services.email_service import send_smtp_email
from backend.app.services.excel_service import (
    export_inventory_excel, export_batches_and_expiry_excel, export_sales_excel
)
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/settings", tags=["Pharmacy Settings & Email"])

@router.get("", response_model=PharmacySettingResponse)
def get_settings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    setting = db.query(PharmacySetting).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Settings not configured")
    return setting

@router.put("", response_model=PharmacySettingResponse)
def update_settings(
    settings_in: PharmacySettingUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin"]))
):
    setting = db.query(PharmacySetting).first()
    if not setting:
        setting = PharmacySetting()
        db.add(setting)

    for field, val in settings_in.dict().items():
        # Do not overwrite password with empty string if not changed
        if field == "smtp_password" and not val:
            continue
        setattr(setting, field, val)

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE_SETTINGS",
        module="SETTINGS",
        details="Updated pharmacy profile & system configuration"
    )
    db.add(audit)
    db.commit()
    db.refresh(setting)
    return setting

@router.post("/test-email")
def test_smtp_configuration(
    test_in: SmtpTestRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin"]))
):
    subject = "Baalaji Pharmacy - SMTP Test Email"
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #1e293b;">
            <div style="background-color: #0f766e; color: white; padding: 15px; border-radius: 6px;">
                <h2 style="margin: 0;">Baalaji Medicals & Pharmacy</h2>
                <p style="margin: 5px 0 0 0;">Automated Notification System</p>
            </div>
            <div style="padding: 20px 0;">
                <p>Hello,</p>
                <p>This is a test notification confirming that your SMTP email settings are working correctly.</p>
                <p><b>Server Time:</b> {date.today()}</p>
                <p><b>Triggered By:</b> {current_user.full_name} ({current_user.username})</p>
            </div>
            <hr style="border: 0; border-top: 1px solid #cbd5e1;" />
            <p style="font-size: 11px; color: #64748b;">This email was sent automatically from your Pharmacy Management Software.</p>
        </body>
    </html>
    """
    res = send_smtp_email(
        db=db,
        subject=subject,
        body_html=body_html,
        recipient_email=test_in.test_recipient,
        notification_type="SMTP_TEST"
    )
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@router.post("/send-alert-email/{alert_type}")
def send_on_demand_alert_email(
    alert_type: str, # "low-stock", "expiry", "daily-sales"
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist"]))
):
    setting = db.query(PharmacySetting).first()
    recipient = setting.alert_email_recipient if setting else ""
    if not recipient:
        raise HTTPException(status_code=400, detail="No alert recipient email configured in Settings.")

    today = date.today()

    if alert_type == "low-stock":
        meds = db.query(Medicine).filter(Medicine.is_active == True).all()
        low_stock_meds = [m for m in meds if sum(b.quantity for b in m.batches if b.status != "EXPIRED") <= m.min_stock_level]
        buf = export_inventory_excel(low_stock_meds)
        subject = f"Urgent: Low Stock Alert - {today.strftime('%d-%b-%Y')}"
        body = f"""
        <h2>Baalaji Pharmacy - Low Stock Alert</h2>
        <p>The system has detected <b>{len(low_stock_meds)}</b> medicine(s) running low on stock.</p>
        <p>Attached is the updated Excel sheet with suggested reorders.</p>
        """
        res = send_smtp_email(db, subject, body, recipient, "LOW_STOCK_REPORT", buf, f"Low_Stock_{today}.xlsx")

    elif alert_type == "expiry":
        batches = db.query(MedicineBatch).filter(MedicineBatch.quantity > 0).all()
        buf = export_batches_and_expiry_excel(batches)
        subject = f"Alert: Medicine Expiry Report - {today.strftime('%d-%b-%Y')}"
        body = """
        <h2>Baalaji Pharmacy - Expiry Monitoring Report</h2>
        <p>Please find attached the current batch expiry tracking sheet for near-expiry and expired medicines.</p>
        """
        res = send_smtp_email(db, subject, body, recipient, "EXPIRY_REPORT", buf, f"Expiry_Report_{today}.xlsx")

    elif alert_type == "daily-sales":
        sales = db.query(Sale).filter(Sale.invoice_date == today, Sale.status == "COMPLETED").all()
        buf = export_sales_excel(sales)
        tot_rev = sum(float(s.net_amount or 0) for s in sales)
        subject = f"Daily Sales Summary - {today.strftime('%d-%b-%Y')}"
        body = f"""
        <h2>Baalaji Pharmacy - Daily Sales Report</h2>
        <p>Total Bills: <b>{len(sales)}</b> | Total Revenue: <b>₹{tot_rev:.2f}</b></p>
        <p>Detailed sales transactions are attached in the Excel report.</p>
        """
        res = send_smtp_email(db, subject, body, recipient, "DAILY_SALES_REPORT", buf, f"Sales_Summary_{today}.xlsx")

    else:
        raise HTTPException(status_code=400, detail="Invalid alert type.")

    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@router.get("/logs/audit")
def get_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin"]))
):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    return logs

@router.get("/logs/notifications")
def get_notification_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin"]))
):
    logs = db.query(NotificationLog).order_by(NotificationLog.id.desc()).limit(limit).all()
    return logs
