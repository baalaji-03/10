from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models import (
    Sale, SaleItem, SalesReturn, Purchase, PurchaseReturn, Expense
)
from backend.app.auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["Reports & Analytics"])

@router.get("/financial")
def get_financial_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    sales_q = db.query(Sale).filter(Sale.status == "COMPLETED")
    purchases_q = db.query(Purchase).filter(Purchase.status == "CONFIRMED")
    s_ret_q = db.query(SalesReturn)
    p_ret_q = db.query(PurchaseReturn)
    exp_q = db.query(Expense)

    if start_date:
        sales_q = sales_q.filter(Sale.invoice_date >= start_date)
        purchases_q = purchases_q.filter(Purchase.invoice_date >= start_date)
        s_ret_q = s_ret_q.filter(SalesReturn.return_date >= start_date)
        p_ret_q = p_ret_q.filter(PurchaseReturn.return_date >= start_date)
        exp_q = exp_q.filter(Expense.expense_date >= start_date)

    if end_date:
        sales_q = sales_q.filter(Sale.invoice_date <= end_date)
        purchases_q = purchases_q.filter(Purchase.invoice_date <= end_date)
        s_ret_q = s_ret_q.filter(SalesReturn.return_date <= end_date)
        p_ret_q = p_ret_q.filter(PurchaseReturn.return_date <= end_date)
        exp_q = exp_q.filter(Expense.expense_date <= end_date)

    # 1. Total Sales Revenue
    gross_sales = float(sales_q.with_entities(func.coalesce(func.sum(Sale.net_amount), 0)).scalar() or 0)
    sales_cogs = float(sales_q.with_entities(func.coalesce(func.sum(Sale.total_cost_of_goods), 0)).scalar() or 0)
    sales_count = sales_q.count()

    # 2. Sales Returns
    sales_refunds = float(s_ret_q.with_entities(func.coalesce(func.sum(SalesReturn.total_refund_amount), 0)).scalar() or 0)
    net_sales_revenue = max(0.0, gross_sales - sales_refunds)

    # 3. Purchases & Purchase Returns
    purchases_total = float(purchases_q.with_entities(func.coalesce(func.sum(Purchase.total_amount), 0)).scalar() or 0)
    purchase_returns_total = float(p_ret_q.with_entities(func.coalesce(func.sum(PurchaseReturn.total_refund_amount), 0)).scalar() or 0)
    net_purchases = max(0.0, purchases_total - purchase_returns_total)

    # 4. Profitability
    # Gross Profit = Net Sales Revenue - COGS
    gross_profit = float(sales_q.with_entities(func.coalesce(func.sum(Sale.gross_profit), 0)).scalar() or 0)
    total_expenses = float(exp_q.with_entities(func.coalesce(func.sum(Expense.amount), 0)).scalar() or 0)
    net_profit = gross_profit - total_expenses

    # 5. GST Breakdown
    cgst_sales = float(sales_q.with_entities(func.coalesce(func.sum(Sale.cgst_amount), 0)).scalar() or 0)
    sgst_sales = float(sales_q.with_entities(func.coalesce(func.sum(Sale.sgst_amount), 0)).scalar() or 0)
    igst_sales = float(sales_q.with_entities(func.coalesce(func.sum(Sale.igst_amount), 0)).scalar() or 0)
    total_tax_collected = float(sales_q.with_entities(func.coalesce(func.sum(Sale.tax_amount), 0)).scalar() or 0)

    cgst_pur = float(purchases_q.with_entities(func.coalesce(func.sum(Purchase.cgst_amount), 0)).scalar() or 0)
    sgst_pur = float(purchases_q.with_entities(func.coalesce(func.sum(Purchase.sgst_amount), 0)).scalar() or 0)
    total_tax_paid_purchase = float(purchases_q.with_entities(func.coalesce(func.sum(Purchase.tax_amount), 0)).scalar() or 0)

    net_gst_liability = max(0.0, total_tax_collected - total_tax_paid_purchase)

    # 6. Payment Method Breakdown
    methods = ["CASH", "UPI", "CARD", "CREDIT"]
    payment_distribution = {}
    for m in methods:
        val = sales_q.filter(Sale.payment_method == m).with_entities(
            func.coalesce(func.sum(Sale.net_amount), 0)
        ).scalar() or 0
        payment_distribution[m] = float(val)

    # 7. Best Selling Medicines
    top_items_query = db.query(
        SaleItem.medicine_name,
        func.sum(SaleItem.quantity).label("units_sold"),
        func.sum(SaleItem.total_amount).label("revenue")
    ).join(Sale, SaleItem.sale_id == Sale.id).filter(Sale.status == "COMPLETED")

    if start_date:
        top_items_query = top_items_query.filter(Sale.invoice_date >= start_date)
    if end_date:
        top_items_query = top_items_query.filter(Sale.invoice_date <= end_date)

    top_items = top_items_query.group_by(SaleItem.medicine_name).order_by(func.sum(SaleItem.quantity).desc()).limit(10).all()
    best_sellers = [
        {
            "medicine_name": itm[0],
            "units_sold": int(itm[1]),
            "revenue": float(itm[2])
        }
        for itm in top_items
    ]

    return {
        "summary": {
            "gross_sales": gross_sales,
            "sales_refunds": sales_refunds,
            "net_sales_revenue": net_sales_revenue,
            "sales_count": sales_count,
            "purchases_total": purchases_total,
            "purchase_returns_total": purchase_returns_total,
            "net_purchases": net_purchases,
            "cogs": sales_cogs,
            "gross_profit": gross_profit,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
            "gross_margin_percent": round((gross_profit / net_sales_revenue * 100), 1) if net_sales_revenue > 0 else 0.0
        },
        "gst_summary": {
            "output_tax": {
                "cgst": cgst_sales,
                "sgst": sgst_sales,
                "igst": igst_sales,
                "total": total_tax_collected
            },
            "input_tax_credit": {
                "cgst": cgst_pur,
                "sgst": sgst_pur,
                "total": total_tax_paid_purchase
            },
            "net_payable_gst": net_gst_liability
        },
        "payment_methods": payment_distribution,
        "best_sellers": best_sellers
    }
