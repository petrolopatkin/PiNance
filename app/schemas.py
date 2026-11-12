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
    user_id: int


class TransactionCreate(BaseModel):
    transaction_type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0)
    description: str | None = None
    transaction_date: date
    user_id: int 


class TransactionUpdate(BaseModel):
    transaction_type: Literal["income", "expense"] | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    description: str | None = None
    transaction_date: date | None = None


class TransactionReplace(BaseModel):
    transaction_type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0)
    description: str | None = None
    transaction_date: date


class UserSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal