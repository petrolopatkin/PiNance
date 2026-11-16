from fastapi import FastAPI, HTTPException, Depends, Query, Response
from datetime import date
from decimal import Decimal
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Transaction, User, Category
from app.schemas import TransactionRead, TransactionCreate, TransactionUpdate, TransactionReplace, UserSummary, CategoryRead, CategoryCreate, CategoryUpdate

app = FastAPI()


def get_total(db: Session, user_id: int, transaction_type:str):
    statement = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == transaction_type
        )

    result = db.execute(statement)
    summary = result.scalar_one()

    return summary


@app.get("/users/{user_id}/transactions", response_model=list[TransactionRead])
def get_transactions_by_user_and_date(user_id: int, 
date_from: date | None = None, date_to: date | None = None, min_amount: Decimal | None = None,
max_amount: Decimal | None = None, skip: int = Query(default=0, ge=0), limit: int = Query(default=20, ge=1, le=100),
db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="Start date must be earlier than or equal to end date"
        )

    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(
            status_code=422,
            detail="Minimal amount cannot be bigger than maximum"
        )
    
    statement = select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.transaction_date.desc(), Transaction.id.desc())

    if date_from is not None:
        statement = statement.where(Transaction.transaction_date >= date_from)

    if date_to is not None:
        statement = statement.where(Transaction.transaction_date <= date_to)

    if min_amount is not None:
        statement = statement.where(Transaction.amount >= min_amount)

    if max_amount is not None:
        statement = statement.where(Transaction.amount <= max_amount)

    statement = statement.offset(skip).limit(limit)
    result = db.execute(statement)
    transactions = result.scalars().all()

    return transactions


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/transactions", response_model=list[TransactionRead])
def get_transactions(transaction_type: str | None = None, sort: str | None = None, 
db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=100)):
    statement = select(Transaction)

    if transaction_type is not None:
        statement = statement.where(Transaction.transaction_type == transaction_type)

    if sort == "amount":
        statement = statement.order_by(Transaction.amount.desc())

    statement = statement.limit(limit)
    result = db.execute(statement)
    transactions_result = result.scalars().all()

    return transactions_result


@app.get("/transactions/{transaction_id}", response_model=TransactionRead)
def get_transaction_by_id(transaction_id: int, db: Session = Depends(get_db)):
    statement = select(Transaction).where(Transaction.id == transaction_id)

    result = db.execute(statement)
    transaction = result.scalar_one_or_none()

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction


@app.get("/users/{user_id}/summary", response_model=UserSummary)
def get_user_summary(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    total_income = get_total(db, user_id, "income")
    total_expense = get_total(db, user_id, "expense")

    balance = total_income - total_expense

    return UserSummary(
        total_income=total_income,
        total_expenses=total_expense,
        balance=balance
    )


@app.get("/users/{user_id}/categories", response_model=list[CategoryRead])
def get_categories_by_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    statement = select(Category).where(or_(Category.user_id == user_id, Category.user_id.is_(None)))
    result = db.execute(statement)
    categories = result.scalars().all()

    return categories


@app.post("/transactions", response_model=TransactionRead, status_code=201)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    if transaction.user_id is not None:
        user =  db.get(User, transaction.user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

    new_transaction = Transaction(**transaction.model_dump())

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction


@app.post("/users/{user_id}/categories", response_model=CategoryRead, status_code=201)
def create_category(user_id: int, category: CategoryCreate, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    new_category = Category(user_id=user_id, **category.model_dump())

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category


@app.patch("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, transaction: TransactionUpdate, 
db: Session = Depends(get_db)):
    statement = select(Transaction).where(Transaction.id == transaction_id)
    result = db.execute(statement)
    db_transaction = result.scalar_one_or_none()

    if db_transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    update_data = transaction.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_transaction, key, value)

    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction


@app.patch("/users/{user_id}/categories/{category_id}", response_model=CategoryRead)
def update_category(user_id: int, category_id: int, category: CategoryUpdate, 
db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db_category = db.get(Category, category_id)

    if db_category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    if db_category.user_id is None:
        raise HTTPException(
            status_code=403,
            detail="Standart categories cannot be modified"
        )

    if db_category.user_id != user_id:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    category_data = category.model_dump(exclude_unset=True)

    if not category_data or category_data.get("name") is None:
        raise HTTPException(
            status_code=422,
            detail="A valid category name must be provided"
        )
    
    for key, value in category_data.items():
            setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)

    return db_category
    

@app.put("/transactions/{transaction_id}", response_model=TransactionRead)
def replace_transaction(transaction_id: int, transaction: TransactionReplace,
db: Session = Depends(get_db)):
    statement = select(Transaction).where(Transaction.id == transaction_id)
    result = db.execute(statement)
    db_transaction = result.scalar_one_or_none()

    if db_transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    update_data = transaction.model_dump()

    for key, value in update_data.items():
        setattr(db_transaction, key, value)

    db.commit()
    db.refresh(db_transaction)

    return db_transaction


@app.delete("/transactions/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    statement = select(Transaction).where(Transaction.id == transaction_id)
    result = db.execute(statement)
    db_transaction = result.scalar_one_or_none()

    if db_transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    db.delete(db_transaction)
    db.commit()

    return Response(status_code=204)


@app.delete("/users/{user_id}/categories/{category_id}", status_code=204)
def delete_category(user_id: int, category_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db_category = db.get(Category, category_id)

    if db_category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    if db_category.user_id is None:
        raise HTTPException(
            status_code=403,
            detail="Standart categories cannot be deleted"
        )

    if db_category.user_id != user_id:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    statement = select(Transaction).where(Transaction.category_id == category_id)
    result = db.execute(statement)
    transaction = result.scalar_one_or_none()

    if transaction is not None:
        raise HTTPException(
            status_code=409,
            detail="This category contains some transactions. Delete them before deleting the category"
        )

    db.delete(db_category)
    db.commit()

    return Response(status_code=204)