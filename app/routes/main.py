import csv
import io
from datetime import date, datetime

from flask import Blueprint, flash, jsonify, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Budget, Category, Transaction
from app.services.analytics import summarize
from app.services.categorizer import categorize

main_bp = Blueprint("main", __name__)


def dashboard_data():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.transaction_date.desc()).all()
    income = sum(item.amount for item in transactions if item.type == "income")
    expenses = sum(item.amount for item in transactions if item.type == "expense")
    month = date.today().strftime("%Y-%m")
    monthly = [item for item in transactions if item.transaction_date.strftime("%Y-%m") == month]
    monthly_income = sum(item.amount for item in monthly if item.type == "income")
    monthly_expenses = sum(item.amount for item in monthly if item.type == "expense")
    budgets = Budget.query.filter_by(user_id=current_user.id, month=month).all()
    budget_total = sum(item.budget_amount for item in budgets)
    return {"transactions": transactions, "income": income, "expenses": expenses, "balance": income - expenses, "monthly_income": monthly_income, "monthly_expenses": monthly_expenses, "savings": monthly_income - monthly_expenses, "budgets": budgets, "budget_total": budget_total, "budget_used": monthly_expenses}


@main_bp.get("/")
def landing():
    return render_template("landing.html") if not current_user.is_authenticated else redirect(url_for("main.dashboard"))


@main_bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", data=dashboard_data(), analytics=summarize(current_user.id), active="dashboard")


@main_bp.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions():
    if request.method == "POST":
        kind = request.form.get("type", "expense")
        description = request.form.get("description", "").strip()
        try:
            amount = float(request.form.get("amount", 0))
            transaction_date = datetime.strptime(request.form.get("transaction_date"), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            amount, transaction_date = 0, None
        if amount <= 0 or not description or not transaction_date or kind not in {"expense", "income"}:
            flash("Please enter a valid transaction.", "danger")
        else:
            category = request.form.get("category") or categorize(description) if kind == "expense" else request.form.get("category", "Other")
            db.session.add(Transaction(user_id=current_user.id, type=kind, amount=amount, category=category, description=description, payment_method=request.form.get("payment_method", "Other"), transaction_date=transaction_date))
            db.session.commit()
            flash("Transaction added.", "success")
            return redirect(url_for("main.transactions"))
    query = Transaction.query.filter_by(user_id=current_user.id)
    search = request.args.get("search", "").strip()
    kind = request.args.get("type", "")
    category = request.args.get("category", "")
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))
    if kind in {"expense", "income"}:
        query = query.filter_by(type=kind)
    if category:
        query = query.filter_by(category=category)
    return render_template("transactions.html", transactions=query.order_by(Transaction.transaction_date.desc()).all(), categories=Category.query.filter_by(type="expense").all(), active="transactions", today=date.today().isoformat())


@main_bp.post("/transactions/<int:transaction_id>/delete")
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction deleted.", "success")
    return redirect(request.referrer or url_for("main.transactions"))


@main_bp.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    if request.method == "POST":
        try:
            transaction.amount = float(request.form.get("amount", 0))
            transaction.transaction_date = datetime.strptime(request.form.get("transaction_date"), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("Enter a valid amount and date.", "danger")
            return render_template("edit_transaction.html", transaction=transaction, categories=Category.query.filter_by(type="expense").all(), active="transactions")
        if transaction.amount <= 0 or not request.form.get("description", "").strip():
            flash("Description and a positive amount are required.", "danger")
        else:
            transaction.type = request.form.get("type", transaction.type)
            transaction.category = request.form.get("category", transaction.category)
            transaction.description = request.form["description"].strip()
            transaction.payment_method = request.form.get("payment_method", "Other")
            db.session.commit()
            flash("Transaction updated.", "success")
            return redirect(url_for("main.transactions"))
    return render_template("edit_transaction.html", transaction=transaction, categories=Category.query.filter_by(type="expense").all(), active="transactions")


@main_bp.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    month = request.form.get("month") or request.args.get("month") or date.today().strftime("%Y-%m")
    if request.method == "POST":
        category = request.form.get("category", "Overall")
        amount = float(request.form.get("budget_amount", 0) or 0)
        if amount > 0:
            budget = Budget.query.filter_by(user_id=current_user.id, category=category, month=month).first()
            if budget:
                budget.budget_amount = amount
            else:
                db.session.add(Budget(user_id=current_user.id, category=category, budget_amount=amount, month=month))
            db.session.commit()
            flash("Budget saved.", "success")
        return redirect(url_for("main.budgets", month=month))
    items = Budget.query.filter_by(user_id=current_user.id, month=month).all()
    spent = {category: sum(t.amount for t in Transaction.query.filter_by(user_id=current_user.id, category=category, type="expense").all()) for category in [item.category for item in items]}
    return render_template("budgets.html", budgets=items, spent=spent, month=month, active="budgets")


@main_bp.get("/analytics")
@login_required
def analytics():
    return render_template("analytics.html", analytics=summarize(current_user.id), active="analytics")


@main_bp.get("/reports/export")
@login_required
def export_report():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Amount", "Category", "Description", "Payment method"])
    for item in Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.transaction_date.desc()):
        writer.writerow([item.transaction_date, item.type, item.amount, item.category, item.description, item.payment_method])
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=smart-expense-report.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip() or current_user.name
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        if new_password:
            if not current_user.check_password(current_password) or len(new_password) < 8:
                flash("Current password is incorrect or the new password is too short.", "danger")
                return render_template("profile.html", active="profile")
            current_user.set_password(new_password)
        db.session.commit()
        flash("Profile updated.", "success")
    return render_template("profile.html", active="profile")


@main_bp.get("/settings")
@login_required
def settings():
    return render_template("settings.html", active="settings")
