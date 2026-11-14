from app.database import SessionLocal
from app.models import Category

STANDARD_CATEGORIES = [
    # Expenses
    {"name": "Food", "transaction_type": "expense"},
    {"name": "Transport", "transaction_type": "expense"},
    {"name": "Housing", "transaction_type": "expense"},
    {"name": "Health", "transaction_type": "expense"},
    {"name": "Education", "transaction_type": "expense"},
    {"name": "Entertainment", "transaction_type": "expense"},
    {"name": "Shopping", "transaction_type": "expense"},
    {"name": "Other", "transaction_type": "expense"},

    # Income
    {"name": "Salary", "transaction_type": "income"},
    {"name": "Freelance", "transaction_type": "income"},
    {"name": "Business", "transaction_type": "income"},
    {"name": "Investments", "transaction_type": "income"},
    {"name": "Gifts", "transaction_type": "income"},
    {"name": "Other", "transaction_type": "income"},
]

def seed_categories():
    db = SessionLocal()

    try:
        for category_data in STANDARD_CATEGORIES:
            existing_category = db.query(Category).filter(Category.name == category_data["name"],
            Category.transaction_type == category_data["transaction_type"],
            Category.user_id.is_(None)).first()

            if existing_category is None:
                db.add(Category(**category_data))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_categories()