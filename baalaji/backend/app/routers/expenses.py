from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Expense, AuditLog
from backend.app.schemas import ExpenseCreate, ExpenseResponse
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/expenses", tags=["Operating Expenses"])

@router.get("", response_model=List[ExpenseResponse])
def get_expenses(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Expense)
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    if category:
        query = query.filter(Expense.expense_category == category)
    return query.order_by(Expense.expense_date.desc()).all()

@router.post("", response_model=ExpenseResponse)
def create_expense(
    exp_in: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["Admin", "Pharmacist"]))
):
    expense = Expense(
        expense_category=exp_in.expense_category,
        description=exp_in.description,
        amount=exp_in.amount,
        expense_date=exp_in.expense_date or date.today(),
        payment_method=exp_in.payment_method,
        receipt_reference=exp_in.receipt_reference,
        user_id=current_user.id
    )
    db.add(expense)

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="ADD_EXPENSE",
        module="EXPENSES",
        details=f"Added expense {expense.expense_category}: ₹{expense.amount:.2f}"
    )
    db.add(audit)
    db.commit()
    db.refresh(expense)
    return expense
