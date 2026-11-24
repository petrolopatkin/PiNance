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
    category_id: int | None = None


class TransactionCreate(BaseModel):
    transaction_type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0)
    description: str | None = None
    transaction_date: date
    user_id: int 
    category_id: int | None = None


class TransactionUpdate(BaseModel):
    transaction_type: Literal["income", "expense"] | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    description: str | None = None
    transaction_date: date | None = None
    category_id: int | None = None


class TransactionReplace(BaseModel):
    transaction_type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0)
    description: str | None = None
    transaction_date: date
    category_id: int | None = None


class UserSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str 
    password: str = Field(min_length=8)


class UserRead(BaseModel):
    model_config = {
        "from_attributes": True
    }

    id: int
    username: str
    email: str


class UserLogin(BaseModel):
    email: str
    password: str = Field(min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str


class CategoryRead(BaseModel):
    model_config = {
        "from_attributes": True
    }

    id: int
    name: str
    transaction_type: str
    user_id: int | None


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    transaction_type: Literal["income", "expense"]


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)