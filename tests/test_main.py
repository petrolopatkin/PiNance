from fastapi.testclient import TestClient
from app.main import app
import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine, Column, BigInteger, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import Base, Transaction
from app.database import get_db

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False
)

Table(
    "users",
    Base.metadata,
    Column("id", BigInteger, primary_key=True)
)

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
    transaction = Transaction(
        id = 1,
        transaction_type="spending",
        amount=Decimal("25.50"),
        description="Lunch",
        transaction_date=date(2026, 11, 6),
        user_id=None
    )

    test_db.add(transaction)
    test_db.commit()

    response = test_client.get("/transactions")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 1


def test_transactions_filtered_by_type(test_client, test_db):
    transactions = [Transaction(
        id=2,
        transaction_type="income",
        amount=Decimal("50"),
        description="Part-time Job",
        transaction_date=date(2026, 11, 6),
        user_id=None
    ),
    Transaction(
        id=3,
        transaction_type="spending",
        amount=Decimal("15.50"),
        description="Lunch",
        transaction_date=date(2026, 11, 6),
        user_id=None
    )]

    test_db.add_all(transactions)
    test_db.commit()

    response = test_client.get("/transactions?transaction_type=income")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 2


def test_transactions_sorted_by_amount(test_client, test_db):
    transactions = [
        Transaction(
        id=2,
        transaction_type="income",
        amount=Decimal("50"),
        description="Part-time Job",
        transaction_date=date(2026, 11, 6),
        user_id=None
    ),
    Transaction(
        id=3,
        transaction_type="spending",
        amount=Decimal("15.50"),
        description="Lunch",
        transaction_date=date(2026, 11, 6),
        user_id=None),
    Transaction(
        id=4,
        transaction_type="spending",
        amount=Decimal("42.40"),
        description="Coat",
        transaction_date = date(2026, 11, 6),
        user_id=None
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
    transactions = Transaction(
        id=4,
        transaction_type="spending",
        amount=Decimal("42.40"),
        description="Coat",
        transaction_date = date(2026, 11, 6),
        user_id=None
    )

    test_db.add(transactions)
    test_db.commit()

    response = test_client.get("/transactions/4")

    assert response.status_code == 200

    result = response.json()

    assert result["id"] == 4
    assert result["description"] == "Coat"


def test_transactions_transaction_id_rejects(test_client, test_db):
    transactions = Transaction(
        id=4,
        transaction_type="spending",
        amount=Decimal("42.40"),
        description="Coat",
        transaction_date = date(2026, 11, 6),
        user_id=None
    )

    test_db.add(transactions)
    test_db.commit()

    response = test_client.get("/transactions/5")

    assert response.status_code == 404

    result = response.json()

    assert result["detail"] == "Transaction not found"