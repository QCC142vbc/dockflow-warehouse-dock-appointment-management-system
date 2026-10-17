import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User


TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=test_engine)

    database = TestingSessionLocal()

    try:
        yield database
    finally:
        database.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db):
    admin = User(
        email="admin@test.com",
        hashed_password=hash_password("TestPassword123"),
        full_name="Test Administrator",
        role="ADMIN",
        is_active=True,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    return admin


@pytest.fixture
def admin_token(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user.email,
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


@pytest.fixture
def carrier_user_and_carrier(db):
    from app.models.carrier import Carrier
    from app.models.carrier_user import CarrierUser

    carrier = Carrier(
        company_name="Carrier Test Co",
        registration_number="REG-CARRIER-TEST",
        contact_email="carrier@test.com",
        country="Hungary",
        is_active=True,
    )
    user = User(
        email="carrier_user@test.com",
        hashed_password=hash_password("CarrierPass123"),
        full_name="Carrier Dispatcher",
        role="CARRIER",
        is_active=True,
    )
    db.add_all([carrier, user])
    db.flush()

    cu = CarrierUser(user_id=user.id, carrier_id=carrier.id)
    db.add(cu)
    db.commit()
    db.refresh(user)
    db.refresh(carrier)

    return {"user": user, "carrier": carrier}


@pytest.fixture
def carrier_token(client, carrier_user_and_carrier):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": carrier_user_and_carrier["user"].email,
            "password": "CarrierPass123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def warehouse_manager_user_and_wh(db):
    from app.models.warehouse import Warehouse
    from app.models.warehouse_user import WarehouseUser

    warehouse = Warehouse(
        name="Manager Test Hub",
        code="WH-MGR-01",
        address="Manager St 1",
        city="Budapest",
        postal_code="1000",
        country="Hungary",
        timezone="Europe/Budapest",
        is_active=True,
    )
    user = User(
        email="manager@test.com",
        hashed_password=hash_password("ManagerPass123"),
        full_name="Warehouse Manager",
        role="WAREHOUSE_MANAGER",
        is_active=True,
    )
    db.add_all([warehouse, user])
    db.flush()

    wu = WarehouseUser(user_id=user.id, warehouse_id=warehouse.id)
    db.add(wu)
    db.commit()
    db.refresh(user)
    db.refresh(warehouse)

    return {"user": user, "warehouse": warehouse}


@pytest.fixture
def warehouse_manager_token(client, warehouse_manager_user_and_wh):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": warehouse_manager_user_and_wh["user"].email,
            "password": "ManagerPass123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]