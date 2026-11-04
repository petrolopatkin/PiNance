from fastapi import FastAPI, HTTPException

app = FastAPI()
transactions = [
            {
                "id": 1,
                "type": "expense",
                "amount": 25.50,
                "description": "Groceries"
            },
            {
                "id": 2,
                "type": "income",
                "amount": 1200,
                "description": "Salary"
            }
        ]

@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/transactions")
def get_transactions(transaction_type: str | None = None, sort: str | None = None):
    result = transactions

    if transaction_type is not None:
        result = [
            transaction 
            for transaction in transactions 
            if transaction["type"] == transaction_type
        ]

    if sort == "amount":
        result = sorted(
            result,
            key=lambda transaction: transaction["amount"],
            reverse=True
        )

    return result


@app.get("/transactions/{transaction_id}")
def get_transaction_by_id(transaction_id: int):
    for transaction in transactions:
        if transaction["id"] == transaction_id:
            return transaction

    raise HTTPException(
        status_code=404,
        detail="Transaction not found"
        )