from datetime import date

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.models import Budget, Category, Transaction
from app.services.analytics import summarize
from app.services.categorizer import categorize

api_bp = Blueprint("api", __name__, url_prefix="/api")


def transaction_json(item):
    return {"id": item.id, "type": item.type, "amount": item.amount, "category": item.category, "description": item.description, "payment_method": item.payment_method, "transaction_date": item.transaction_date.isoformat()}


@api_bp.get("/transactions")
@login_required
def get_transactions():
    return jsonify([transaction_json(item) for item in Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.transaction_date.desc())])


@api_bp.post("/transactions")
@login_required
def create_transaction():
    payload = request.get_json(silent=True) or {}
    try:
        amount = float(payload["amount"])
        transaction_date = date.fromisoformat(payload.get("transaction_date", date.today().isoformat()))
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "amount and valid transaction_date are required"}), 400
    kind = payload.get("type", "expense")
    description = str(payload.get("description", "")).strip()
    if kind not in {"expense", "income"} or amount <= 0 or not description:
        return jsonify({"error": "invalid transaction fields"}), 400
    item = Transaction(user_id=current_user.id, type=kind, amount=amount, category=payload.get("category") or categorize(description), description=description, payment_method=payload.get("payment_method", "Other"), transaction_date=transaction_date)
    db.session.add(item)
    db.session.commit()
    return jsonify(transaction_json(item)), 201


@api_bp.route("/transactions/<int:item_id>", methods=["PUT", "DELETE"])
@login_required
def modify_transaction(item_id):
    item = Transaction.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    if request.method == "DELETE":
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "deleted"})
    payload = request.get_json(silent=True) or {}
    for field in ("type", "category", "description", "payment_method"):
        if field in payload:
            setattr(item, field, payload[field])
    if "amount" in payload:
        item.amount = float(payload["amount"])
    if "transaction_date" in payload:
        item.transaction_date = date.fromisoformat(payload["transaction_date"])
    db.session.commit()
    return jsonify(transaction_json(item))


@api_bp.get("/dashboard")
@login_required
def dashboard_api():
    items = Transaction.query.filter_by(user_id=current_user.id).all()
    income = sum(item.amount for item in items if item.type == "income")
    expense = sum(item.amount for item in items if item.type == "expense")
    return jsonify({"total_income": income, "total_expenses": expense, "balance": income - expense, "recent_transactions": [transaction_json(item) for item in items[-5:]]})


@api_bp.get("/analytics")
@login_required
def analytics_api():
    return jsonify(summarize(current_user.id))


@api_bp.get("/categories")
def categories_api():
    return jsonify([{"id": item.id, "name": item.name, "type": item.type} for item in Category.query.order_by(Category.type, Category.name)])


@api_bp.get("/budgets")
@login_required
def budgets_api():
    return jsonify([{ "id": item.id, "category": item.category, "amount": item.budget_amount, "month": item.month } for item in Budget.query.filter_by(user_id=current_user.id)])
