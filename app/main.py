from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Transaction
from app.schemas import TransactionRead

app = FastAPI()

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