# Smart Expense Tracker

**Track Smarter. Spend Better. Save More.**

Smart Expense Tracker is a modern Flask application for understanding income, expenses, budgets, and spending habits in one calm financial workspace. It includes secure authentication, smart keyword categorization, Pandas-powered analytics, interactive charts, CSV reporting, and a JSON REST API.

## Features

- User registration, login, logout, profile editing, and password changes
- Expense and income CRUD workflows with ownership protection
- Automatic categorization for common descriptions such as Zomato, Uber, Netflix, and Amazon
- Dashboard for balances, monthly income, monthly expenses, savings, recent activity, and budget health
- Category breakdown and monthly trend charts with Chart.js
- Overall and category-specific monthly budgets with 80% warning states
- Generated insights for top category, spending change, savings rate, and payment method
- Search and filter transaction history; export all records to CSV
- Responsive light and dark UI for desktop, tablet, and mobile
- SQLite by default with a PostgreSQL-ready `DATABASE_URL`

## Technologies

Python, Flask, Flask-Login, Flask-SQLAlchemy, SQLite, Pandas, NumPy-compatible analytics stack, Chart.js, Bootstrap 5, Font Awesome, and vanilla JavaScript.

## Run in GitHub Codespaces

```bash
pip install -r requirements.txt
python run.py
```

Open port 5000 in the Ports panel. On the first run, the app creates `instance/smart_expenses.db`, category records, and a complete demo account:

| Email | Password |
| --- | --- |
| `demo@smartexpense.app` | `demo1234` |

For production, set a strong `SECRET_KEY` and a managed `DATABASE_URL` in the environment. Copy `.env.example` as a reference.

## Project structure

```text
smart-expense-tracker/
├── app/
│   ├── models.py
│   ├── routes/                 # auth, HTML, and JSON API blueprints
│   ├── services/              # analytics, categorization, and demo seed data
│   ├── static/                # CSS and JavaScript
│   └── templates/             # landing, auth, dashboard, and app pages
├── instance/                  # local SQLite database (created at runtime)
├── config.py
├── requirements.txt
└── run.py
```

## API documentation

Protected endpoints use the current Flask-Login session and return JSON.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/transactions` | List the signed-in user's transactions |
| `POST` | `/api/transactions` | Create a transaction |
| `PUT` | `/api/transactions/<id>` | Update an owned transaction |
| `DELETE` | `/api/transactions/<id>` | Delete an owned transaction |
| `GET` | `/api/dashboard` | Return totals and recent transactions |
| `GET` | `/api/analytics` | Return category, monthly, trend, and insight data |
| `GET` | `/api/categories` | Return available categories |
| `GET` | `/api/budgets` | List the signed-in user's budgets |

Example request body for `POST /api/transactions`:

```json
{
	"type": "expense",
	"amount": 799,
	"description": "Netflix subscription",
	"payment_method": "Credit card",
	"transaction_date": "2026-09-08"
}
```

## Screenshots

Screenshots can be added here after deployment:

- Landing page
- Dashboard overview
- Analytics and budget planner
- Mobile responsive view

## Architecture notes

Route handlers stay thin while categorization, seeding, and analytics live in services. SQLAlchemy models use foreign keys and cascading relationships, and every protected query scopes records to the authenticated user. The default SQLite URI can be replaced with PostgreSQL without changing model or route code.
