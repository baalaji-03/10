from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.database import get_db
from backend.app.models import Customer, Sale, AuditLog
from backend.app.schemas import CustomerCreate, CustomerUpdate, CustomerResponse
from backend.app.auth import get_current_user

router = APIRouter(prefix="/api/customers", tags=["Customers"])

@router.get("", response_model=List[CustomerResponse])
def get_customers(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Customer)
    if search:
        s_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Customer.name.ilike(s_fmt),
                Customer.mobile.ilike(s_fmt),
                Customer.customer_code.ilike(s_fmt)
            )
        )
    return query.order_by(Customer.name).all()

@router.get("/{customer_id}/history")
def get_customer_history(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    sales = db.query(Sale).filter(Sale.customer_id == customer_id).order_by(Sale.id.desc()).all()
    invoices_data = []

    for s in sales:
        items_summary = [
            f"{itm.medicine_name} ({itm.quantity}x) [Batch: {itm.batch_number}]"
            for itm in s.items
        ]
        invoices_data.append({
            "sale_id": s.id,
            "invoice_number": s.invoice_number,
            "invoice_date": s.invoice_date.strftime("%d-%m-%Y") if s.invoice_date else "",
            "invoice_time": s.invoice_time.strftime("%I:%M %p") if s.invoice_time else "",
            "net_amount": float(s.net_amount or 0),
            "payment_method": s.payment_method,
            "payment_status": s.payment_status,
            "items_count": len(s.items),
            "items_summary": items_summary
        })

    return {
        "customer": {
            "id": customer.id,
            "customer_code": customer.customer_code,
            "name": customer.name,
            "mobile": customer.mobile,
            "email": customer.email,
            "address": customer.address,
            "gender": customer.gender,
            "total_purchases_count": len(sales),
            "total_spend": sum(float(s.net_amount or 0) for s in sales)
        },
        "invoices": invoices_data
    }

@router.post("", response_model=CustomerResponse)
def create_customer(
    cust_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Duplicate check on mobile
    existing = db.query(Customer).filter(Customer.mobile == cust_in.mobile.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Customer with mobile number '{cust_in.mobile}' already exists ({existing.name}).")

    code_num = db.query(Customer).count() + 1
    c_code = f"CUST-{code_num:04d}"

    cust = Customer(
        customer_code=c_code,
        name=cust_in.name.strip(),
        mobile=cust_in.mobile.strip(),
        email=cust_in.email,
        address=cust_in.address,
        date_of_birth=cust_in.date_of_birth,
        gender=cust_in.gender or "Other",
        notes=cust_in.notes
    )
    db.add(cust)
    db.commit()
    db.refresh(cust)

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE_CUSTOMER",
        module="CUSTOMERS",
        details=f"Registered customer {cust.name} ({cust.mobile})"
    )
    db.add(audit)
    db.commit()

    return cust

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    cust_in: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    cust = db.query(Customer).filter(Customer.id == customer_id).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    for field, val in cust_in.model_dump(exclude_unset=True).items():
        setattr(cust, field, val)

    db.commit()
    db.refresh(cust)
    return cust
