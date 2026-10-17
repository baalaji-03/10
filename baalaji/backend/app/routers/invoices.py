from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Sale, PharmacySetting
from backend.app.services.invoice_service import generate_pdf_invoice
from backend.app.auth import get_current_user

router = APIRouter(prefix="/api/invoices", tags=["Invoices & Printing"])

@router.get("/{sale_id}/pdf")
def download_invoice_pdf(
    sale_id: int,
    format: str = Query("A4", pattern="^(A4|80mm|58mm)$"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale invoice not found")

    setting = db.query(PharmacySetting).first()
    pdf_buffer = generate_pdf_invoice(sale, setting, format_type=format)

    filename = f"{sale.invoice_number}_{format}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

@router.get("/{sale_id}/print-data")
def get_invoice_print_data(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale invoice not found")

    setting = db.query(PharmacySetting).first()

    items = []
    for itm in sale.items:
        items.append({
            "name": itm.medicine_name,
            "generic": itm.generic_name,
            "hsn": itm.hsn_code or "3004",
            "batch": itm.batch_number,
            "expiry": itm.expiry_date.strftime("%m/%y") if itm.expiry_date else "",
            "qty": itm.quantity,
            "mrp": float(itm.mrp or itm.unit_price),
            "rate": float(itm.unit_price),
            "discount_percent": float(itm.discount_percent or 0),
            "gst_rate": float(itm.gst_rate or 12),
            "total": float(itm.total_amount)
        })

    return {
        "pharmacy": {
            "name": setting.pharmacy_name if setting else "Baalaji Medicals & Healthcare",
            "tagline": setting.tagline if setting else "Your Trusted Pharmacy",
            "address": f"{setting.address_line1}, {setting.address_line2 or ''}, {setting.city} - {setting.postal_code}" if setting else "Chennai",
            "phone": setting.phone if setting else "",
            "email": setting.email if setting else "",
            "gstin": setting.gstin if setting else "",
            "dl_number": setting.dl_number if setting else "",
            "declaration": setting.invoice_declaration if setting else "Goods once sold cannot be returned."
        },
        "sale": {
            "id": sale.id,
            "invoice_number": sale.invoice_number,
            "date": sale.invoice_date.strftime("%d-%m-%Y") if sale.invoice_date else "",
            "time": sale.invoice_time.strftime("%I:%M %p") if sale.invoice_time else "",
            "customer_name": sale.customer_name or "Walk-in Customer",
            "customer_mobile": sale.customer_mobile or "N/A",
            "doctor_name": sale.doctor_name or "Self / None",
            "payment_method": sale.payment_method,
            "payment_status": sale.payment_status,
            "subtotal": float(sale.subtotal or 0),
            "discount": float(sale.discount_amount or 0),
            "taxable": float(sale.taxable_amount or 0),
            "cgst": float(sale.cgst_amount or 0),
            "sgst": float(sale.sgst_amount or 0),
            "igst": float(sale.igst_amount or 0),
            "tax": float(sale.tax_amount or 0),
            "round_off": float(sale.round_off or 0),
            "net_amount": float(sale.net_amount or 0),
            "paid_amount": float(sale.paid_amount or 0),
            "balance_amount": float(sale.balance_amount or 0),
            "cashier": sale.user.full_name if sale.user else "Admin"
        },
        "items": items
    }
