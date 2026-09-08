from datetime import date

import pandas as pd

from app.models import Transaction


def transaction_frame(user_id):
    rows = Transaction.query.filter_by(user_id=user_id).all()
    return pd.DataFrame([{"type": row.type, "amount": row.amount, "category": row.category, "description": row.description, "payment_method": row.payment_method, "date": row.transaction_date.isoformat()} for row in rows])


def summarize(user_id):
    frame = transaction_frame(user_id)
    if frame.empty:
        return {"category_totals": {}, "monthly_totals": {}, "trend": [], "insights": []}
    frame["date"] = pd.to_datetime(frame["date"])
    expenses = frame[frame.type == "expense"].copy()
    incomes = frame[frame.type == "income"].copy()
    category_totals = expenses.groupby("category").amount.sum().round(2).to_dict()
    monthly = expenses.assign(month=expenses.date.dt.strftime("%Y-%m")).groupby("month").amount.sum()
    monthly_totals = {str(key): round(float(value), 2) for key, value in monthly.items()}
    highest = max(category_totals, key=category_totals.get) if category_totals else "No spending yet"
    current_month = pd.Timestamp(date.today()).strftime("%Y-%m")
    current = float(monthly.get(current_month, 0))
    previous_keys = sorted(monthly.index)
    previous = float(monthly.get(previous_keys[-2], 0)) if len(previous_keys) > 1 else 0
    change = ((current - previous) / previous * 100) if previous else 0
    income_total = float(incomes.amount.sum()) if not incomes.empty else 0
    expense_total = float(expenses.amount.sum()) if not expenses.empty else 0
    payment = expenses.payment_method.mode().iloc[0] if not expenses.empty else "N/A"
    return {"category_totals": category_totals, "monthly_totals": monthly_totals, "trend": [{"month": str(key), "amount": round(float(value), 2)} for key, value in monthly.items()], "insights": [f"{highest} is your highest spending category.", f"Spending is {abs(change):.0f}% {'higher' if change >= 0 else 'lower'} than the previous month.", f"Your most used payment method is {payment}.", f"Your savings rate is {((income_total - expense_total) / income_total * 100):.0f}%." if income_total else "Add income to see your savings rate."]}
