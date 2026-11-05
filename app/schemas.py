from datetime import date
from decimal import Decimal
from pydantic import BaseModel

class TransactionRead(BaseModel):
    model_config = {
        "from_attributes": True
    }
    
    id: int
    transaction_type: str
    amount: Decimal
    description: str | None
    transaction_date: date
    user_id: int | None