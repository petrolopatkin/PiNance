from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Literal

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


class TransactionCreate(BaseModel):
    transaction_type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0)
    description: str | None = None
    transaction_date: date
    user_id: int | None = None