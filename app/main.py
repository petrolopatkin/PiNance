from fastapi import FastAPI, HTTPException, Depends, Query, Response
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Transaction, User
from app.schemas import TransactionRead, TransactionCreate, TransactionUpdate, TransactionReplace, UserSummary

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
date_from: date | None = None, date_to: date | None = None, db: Session = Depends(get_db)):
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
    
    statement = select(Transaction).where(Transaction.user_id == user_id)

    if date_from is not None:
        statement = statement.where(Transaction.transaction_date >= date_from)

    if date_to is not None:
        statement = statement.where(Transaction.transaction_date <= date_to)

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