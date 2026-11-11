from fastapi.testclient import TestClient
from app.main import app
import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine, Column, BigInteger, Table, select, func, text, event 
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import Base, Transaction, User
from app.database import get_db

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@event.listens_for(test_engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False
)

Base.metadata.create_all(bind=test_engine)

client = TestClient(app)

def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()

        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_client(test_db):
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


def test_get_transactions(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )

    test_db.add(user)
    test_db.commit()

    transaction = Transaction(
        id = 1,
        transaction_type="expense",
        amount=Decimal("25.50"),
        description="Lunch",
        transaction_date=date(2026, 11, 6),
        user_id=1
    )

    test_db.add(transaction)
    test_db.commit()

    response = test_client.get("/transactions")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 1


def test_transactions_filtered_by_type(test_client, test_db):
    users = [
        User(
            id=2,
            username="Kathy"
        ),
        User(
            id=3,
            username="Mary"
        )
    ]

    test_db.add_all(users)
    test_db.commit()

    transactions = [Transaction(
        id=2,
        transaction_type="income",
        amount=Decimal("50"),
        description="Part-time Job",
        transaction_date=date(2026, 11, 6),
        user_id=2
    ),
    Transaction(
        id=3,
        transaction_type="expense",
        amount=Decimal("15.50"),
        description="Lunch",
        transaction_date=date(2026, 11, 6),
        user_id=3
    )]

    test_db.add_all(transactions)
    test_db.commit()

    response = test_client.get("/transactions?transaction_type=income")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 2


def test_transactions_sorted_by_amount(test_client, test_db):
    users = [
        User(
            id=2,
            username="Kathy"
        ),
        User(
            id=3,
            username="Mary"
        ),
        User(
            id=4,
            username="Daniel"
        )
    ]
    
    test_db.add_all(users)
    test_db.commit()

    transactions = [
        Transaction(
        id=2,
        transaction_type="income",
        amount=Decimal("50"),
        description="Part-time Job",
        transaction_date=date(2026, 11, 6),
        user_id=2
    ),
    Transaction(
        id=3,
        transaction_type="expense",
        amount=Decimal("15.50"),
        description="Lunch",
        transaction_date=date(2026, 11, 6),
        user_id=3),
    Transaction(
        id=4,
        transaction_type="expense",
        amount=Decimal("42.40"),
        description="Coat",
        transaction_date = date(2026, 11, 6),
        user_id=4
    )
    ]

    test_db.add_all(transactions)
    test_db.commit()

    response = test_client.get("/transactions?sort=amount")

    assert response.status_code == 200

    result = response.json()

    assert len(result) == 3
    assert result[0]["id"] == 2
    assert result[1]["id"] == 4
    assert result[2]["id"] == 3


def test_transactions_transaction_id_accepts(test_client, test_db):
    user = User(
        id=4,
        username="Daniel"
    )
        
    test_db.add(user)
    test_db.commit()

    transactions = Transaction(
        id=4,
        transaction_type="expense",
        amount=Decimal("42.40"),
        description="Coat",
        transaction_date = date(2026, 11, 6),
        user_id=4
    )

    test_db.add(transactions)
    test_db.commit()

    response = test_client.get("/transactions/4")

    assert response.status_code == 200

    result = response.json()

    assert result["id"] == 4
    assert result["description"] == "Coat"


def test_transactions_transaction_id_rejects(test_client, test_db):
    user = User(
        id=4,
        username="Daniel"
    )
            
    test_db.add(user)
    test_db.commit()
    
    transactions = Transaction(
        id=4,
        transaction_type="expense",
        amount=Decimal("42.40"),
        description="Coat",
        transaction_date = date(2026, 11, 6),
        user_id=4
    )

    test_db.add(transactions)
    test_db.commit()

    response = test_client.get("/transactions/5")

    assert response.status_code == 404

    result = response.json()

    assert result["detail"] == "Transaction not found"


def test_transactions_limit_one(test_client, test_db):
    users = [
        User(
            id=1,
            username="Peter"
        ),
        User(
            id=2,
            username="Kathy"
        ),
        User(
            id=3,
            username="Mary"
        ),
    ]

    test_db.add_all(users)
    test_db.commit()

    transactions = Transaction(
            id=1,
            transaction_type="expense",
            amount=Decimal("42.40"),
            description="Coat",
            transaction_date = date(2026, 11, 6),
            user_id=1
    ),
    Transaction(
            id=2,
            transaction_type="income",
            amount=Decimal("50"),
            description="Part-time Job",
            transaction_date=date(2026, 11, 6),
            user_id=2
    ),
    Transaction(
            id=3,
            transaction_type="expense",
            amount=Decimal("15.50"),
            description="Lunch",
            transaction_date=date(2026, 11, 6),
            user_id=3
    )

    test_db.add_all(transactions)
    test_db.commit()

    response = test_client.get("/transactions?limit=1")

    assert response.status_code == 200

    result = response.json()

    assert len(result) == 1


def test_transactions_limit_zero(test_client):
    response = test_client.get("/transactions?limit=0")

    assert response.status_code == 422


def test_transactions_limit_more_than_hundred(test_client):
    response = test_client.get("/transactions?limit=101")

    assert response.status_code == 422


def test_transactions_negative_limit(test_client):
    response = test_client.get("/transactions?limit=-1")

    assert response.status_code == 422


def test_transactions_filter_returns_empty_list(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )
    
    test_db.add(user)
    test_db.commit()
    
    transactions = Transaction(
        id=1,
        transaction_type="income",
        amount=Decimal("50.00"),
        description="Part-time Job",
        transaction_date=date(2026, 11, 8),
        user_id=1
    )

    test_db.add(transactions)
    test_db.commit()

    response = test_client.get("/transactions?transaction_type=expense")

    assert response.status_code == 200

    result = response.json()

    assert result == []


def test_post_transactions(test_client, test_db):
    user = User(
        id=2,
        username="Kathy"
    )

    test_db.add(user)
    test_db.commit()

    response = test_client.post("/transactions", json={
        "transaction_type":"expense",
        "amount": 42.50,
        "description": "Lunch",
        "transaction_date": "2026-11-08",
        "user_id": 2
    })

    count = test_db.scalar(select(func.count()).select_from(Transaction))

    assert response.status_code == 201

    result = response.json()

    assert result["id"] > 0
    assert result["transaction_type"] == "expense"
    assert result["amount"] == "42.50"
    assert result["description"] == "Lunch"
    assert result["user_id"] == 2
    assert count == 1


def test_post_transactions_missing_date(test_client):
    response = test_client.post("/transactions", json={
            "transaction_type":"expense",
            "amount": 42.50,
            "description": "Lunch",
            "user_id": 2
    })

    assert response.status_code == 422


def test_post_transactions_rejects_incorrect_amount(test_client):
    response = test_client.post("/transactions", json={
            "transaction_type":"expense",
            "amount": -42.50,
            "description": "Lunch",
            "transaction_date": "2026-11-08",
            "user_id": 2
    })

    assert response.status_code == 422


def test_post_transactions_rejects_incorrect_transaction_type(test_client):
    response = test_client.post("/transactions", json={
            "transaction_type":"gift",
            "amount": 42.50,
            "description": "Lunch",
            "transaction_date": "2026-11-08",
            "user_id": 2
    })

    assert response.status_code == 422


def test_post_transactions_with_nonexistent_user(test_client):
    response = test_client.post("/transactions", json={
        "transaction_type": "expense",
        "amount": 36.50,
        "description": "Parfume",
        "transaction_date": "2026-11-11",
        "user_id": 999
    })

    assert response.status_code == 404


def test_post_transactions_without_user_id(test_client, test_db):
    response = test_client.post("/transactions", json={
        "transaction_type": "expense",
        "amount": 36.50,
        "description": "Parfume",
        "transaction_date": "2026-11-11",
    })

    assert response.status_code == 422

    count = test_db.scalar(
        select(func.count()).select_from(Transaction)
    )

    assert count == 0
    

def test_patch_transactions(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )
    
    test_db.add(user)
    test_db.commit()
    
    transactions = Transaction(
        id=1,
        transaction_type="expense",
        amount=42.00,
        description="Lunch",
        transaction_date=date(2026, 11, 9),
        user_id=1
    )

    test_db.add(transactions)
    test_db.commit()
    
    response = test_client.patch("/transactions/1", json={
        "amount": 45.00
    })

    assert response.status_code == 200

    result = response.json()

    assert result["transaction_type"] == "expense"
    assert result["description"] == "Lunch"
    assert result["amount"] == "45.00"
    assert result["transaction_date"] == "2026-11-09"


def test_patch_rejects_negative_amount(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )
    
    test_db.add(user)
    test_db.commit()

    transactions = Transaction(
            id=1,
            transaction_type="expense",
            amount=42.00,
            description="Lunch",
            transaction_date=date(2026, 11, 9),
            user_id=1
    )

    test_db.add(transactions)
    test_db.commit()

    response = test_client.patch("/transactions/1", json={
        "amount": "-50.00"
    })

    assert response.status_code == 422


def test_patch_rejects_transaction_with_wrong_id(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )
    
    test_db.add(user)
    test_db.commit()

    transactions = Transaction(
                id=1,
                transaction_type="expense",
                amount=42.00,
                description="Lunch",
                transaction_date=date(2026, 11, 9),
                user_id=1
    )

    test_db.add(transactions)
    test_db.commit()

    response = test_client.patch("/transactions/2", json={
        "amount": "45.00"
    })

    assert response.status_code == 404


def test_patch_updates_with_multiple_fields(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )
    
    test_db.add(user)
    test_db.commit()

    transactions = Transaction(
                    id=1,
                    transaction_type="expense",
                    amount=42.00,
                    description="Lunch",
                    transaction_date=date(2026, 11, 9),
                    user_id=1
    )

    test_db.add(transactions)
    test_db.commit()

    response = test_client.patch("/transactions/1", json={
        "amount": "45.00",
        "description": "Bus Ticket",
        "transaction_date": "2026-11-08"
    })

    assert response.status_code == 200

    result = response.json()

    assert result["transaction_type"] == "expense"
    assert result["amount"] == "45.00"
    assert result["description"] == "Bus Ticket"
    assert result["transaction_date"] == "2026-11-08"


def test_put_transactions(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )
    
    test_db.add(user)
    test_db.commit()

    transactions = Transaction(
        id=1,
        transaction_type="expense",
        amount=42.00,
        description="Lunch",
        transaction_date=date(2026, 11, 9),
        user_id=1
    )
    
    test_db.add(transactions)
    test_db.commit()

    response = test_client.put("/transactions/1", json={
        "transaction_type": "expense",
        "amount": "50.00",
        "transaction_date": "2026-11-09"
    })

    assert response.status_code == 200

    result = response.json()

    assert result["transaction_type"] == "expense"
    assert result["amount"] == "50.00"
    assert result["description"] is None
    assert result["transaction_date"] == "2026-11-09"


def test_put_transaction_with_wrong_id(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )
    
    test_db.add(user)
    test_db.commit()
    
    transactions = Transaction(
        id=1,
        transaction_type="expense",
        amount=42.00,
        description="Lunch",
        transaction_date=date(2026, 11, 9),
        user_id=1
    )
        
    test_db.add(transactions)
    test_db.commit()

    response = test_client.put("/transactions/2", json={
        "transaction_type": "expense",
        "amount": "50.00",
        "transaction_date": "2026-11-09"
    })

    assert response.status_code == 404


def test_put_rejects_negative_amount(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )
    
    test_db.add(user)
    test_db.commit()

    transactions = Transaction(
        id=1,
        transaction_type="expense",
        amount=42.00,
        description="Lunch",
        transaction_date=date(2026, 11, 9),
        user_id=1
    )
            
    test_db.add(transactions)
    test_db.commit()
    
    response = test_client.put("/transactions/1", json={
        "transaction_type": "expense",
        "amount": "-50.00",
        "transaction_date": "2026-11-09"
    })
    
    assert response.status_code == 422


def test_delete_transaction(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )
    
    test_db.add(user)
    test_db.commit()

    transactions = Transaction(
        id=1,
        transaction_type="expense",
        amount=42.00,
        description="Lunch",
        transaction_date=date(2026, 11, 9),
        user_id=1
    )
                
    test_db.add(transactions)
    test_db.commit()

    response = test_client.delete("/transactions/1")

    assert response.status_code == 204
    assert test_db.get(Transaction, 1) is None


def test_delete_transaction_with_wrong_id(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )
    
    test_db.add(user)
    test_db.commit()

    transactions = Transaction(
        id=1,
        transaction_type="expense",
        amount=42.00,
        description="Lunch",
        transaction_date=date(2026, 11, 9),
        user_id=1
    )
                    
    test_db.add(transactions)
    test_db.commit()

    response = test_client.delete("/transactions/2")

    assert response.status_code == 404
    assert test_db.get(Transaction, 1) is not None


def test_get_transactions_by_user_without_transactions(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )

    test_db.add(user)
    test_db.commit()

    response = test_client.get("/users/1/transactions")

    assert response.status_code == 200
    assert response.json() == []


def test_get_transactions_by_user(test_client, test_db):
    user = User(
        id=1,
        username="Peter"
    )
    
    test_db.add(user)
    test_db.commit()

    transactions = Transaction(
        id=1,
        transaction_type="expense",
        amount=42.00,
        description="Lunch",
        transaction_date=date(2026, 11, 11),
        user_id=1
    )

    test_db.add(transactions)
    test_db.commit()

    response = test_client.get("/users/1/transactions")

    assert response.status_code == 200

    result = response.json()

    assert len(result) == 1

    transaction = result[0]

    assert transaction["id"] == 1
    assert transaction["transaction_type"] == "expense"
    assert transaction["amount"] == '42.00'
    assert transaction["description"] == "Lunch"
    assert transaction["transaction_date"] == "2026-11-11"


def test_get_transactions_by_non_existed_user(test_client):
    response = test_client.get("/users/999/transactions")

    assert response.status_code == 404