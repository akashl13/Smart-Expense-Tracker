from datetime import date, timedelta

from app import db
from app.models import Budget, Category, Transaction, User


def seed_demo_data():
    categories = {"expense": ["Food", "Transportation", "Shopping", "Entertainment", "Education", "Healthcare", "Bills", "Rent", "Travel", "Other"], "income": ["Salary", "Freelancing", "Business", "Investment", "Gift", "Other"]}
    if not Category.query.first():
        db.session.add_all([Category(name=name, type=kind) for kind, names in categories.items() for name in names])
    demo = User.query.filter_by(email="demo@smartexpense.app").first()
    if demo:
        return
    demo = User(name="Demo User", email="demo@smartexpense.app")
    demo.set_password("demo1234")
    db.session.add(demo)
    db.session.flush()
    today = date.today()
    samples = [("income", 85000, "Salary", "Monthly salary", "Bank transfer", 2), ("expense", 1250, "Food", "Zomato dinner", "UPI", 1), ("expense", 2400, "Transportation", "Uber rides", "UPI", 3), ("expense", 5200, "Shopping", "Amazon essentials", "Credit card", 5), ("expense", 799, "Entertainment", "Netflix subscription", "Credit card", 7), ("expense", 18000, "Rent", "Apartment rent", "Bank transfer", 9), ("expense", 2200, "Bills", "Electricity and internet", "Bank transfer", 12)]
    db.session.add_all([Transaction(user_id=demo.id, type=kind, amount=amount, category=category, description=description, payment_method=payment, transaction_date=today - timedelta(days=offset)) for kind, amount, category, description, payment, offset in samples])
    db.session.add(Budget(user_id=demo.id, category="Overall", budget_amount=45000, month=today.strftime("%Y-%m")))
    db.session.commit()
