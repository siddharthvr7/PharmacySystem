
import pytest
import app as pharmacy


@pytest.fixture(autouse=True)
def reset_data():
    with pharmacy.data_lock:
        pharmacy.medicines.clear()

    yield

    with pharmacy.data_lock:
        pharmacy.medicines.clear()


@pytest.fixture
def client():
    pharmacy.app.config["TESTING"] = True
    with pharmacy.app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["version"] == "v1"


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Add Medicine" in response.data
    assert b"Available Medicines" in response.data
    assert b"Generate Bill" not in response.data
    assert b"Bill History" not in response.data


def test_add_medicine(client):
    response = client.post("/add", data={
        "name": "Paracetamol",
        "price": "10",
        "stock": "20"
    })

    assert response.status_code == 302
    assert pharmacy.medicines["Paracetamol"]["price"] == 10.00
    assert pharmacy.medicines["Paracetamol"]["stock"] == 20


def test_added_medicine_is_displayed(client):
    client.post("/add", data={
        "name": "Paracetamol",
        "price": "10",
        "stock": "20"
    })

    response = client.get("/")
    assert response.status_code == 200
    assert b"Paracetamol" in response.data
    assert b"20" in response.data


def test_adding_existing_medicine_increases_stock(client):
    client.post("/add", data={
        "name": "Paracetamol",
        "price": "10",
        "stock": "20"
    })
    client.post("/add", data={
        "name": "Paracetamol",
        "price": "12",
        "stock": "5"
    })

    assert pharmacy.medicines["Paracetamol"]["price"] == 12.00
    assert pharmacy.medicines["Paracetamol"]["stock"] == 25


@pytest.mark.parametrize("data", [
    {"name": "", "price": "10", "stock": "5"},
    {"name": "Paracetamol", "price": "0", "stock": "5"},
    {"name": "Paracetamol", "price": "10", "stock": "-1"},
    {"name": "Paracetamol", "price": "abc", "stock": "5"},
])
def test_invalid_medicine_is_rejected(client, data):
    response = client.post("/add", data=data)
    assert response.status_code == 400


def test_billing_routes_are_not_available(client):
    response = client.post("/bill", data={
        "name": "Paracetamol",
        "quantity": "1"
    })
    assert response.status_code == 404

    response = client.get("/bills/1")
    assert response.status_code == 404
