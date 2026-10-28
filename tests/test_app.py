
import pytest
import app as pharmacy


@pytest.fixture(autouse=True)
def reset_data():
    with pharmacy.data_lock:
        pharmacy.medicines.clear()
        pharmacy.bills.clear()

    yield

    with pharmacy.data_lock:
        pharmacy.medicines.clear()
        pharmacy.bills.clear()


@pytest.fixture
def client():
    pharmacy.app.config["TESTING"] = True
    with pharmacy.app.test_client() as client:
        yield client


def add_test_medicine(client, stock=20, price=10):
    return client.post("/add", data={
        "name": "Paracetamol",
        "price": str(price),
        "stock": str(stock)
    })


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["version"] == "v2"


def test_home_page_has_inventory_and_billing(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Add Medicine" in response.data
    assert b"Available Medicines" in response.data
    assert b"Generate Bill" in response.data
    assert b"Bill History" not in response.data


def test_add_medicine(client):
    response = add_test_medicine(client)
    assert response.status_code == 302
    assert pharmacy.medicines["Paracetamol"]["price"] == 10.00
    assert pharmacy.medicines["Paracetamol"]["stock"] == 20


def test_added_medicine_is_displayed(client):
    add_test_medicine(client)
    response = client.get("/")
    assert b"Paracetamol" in response.data
    assert b"20" in response.data


def test_adding_existing_medicine_increases_stock(client):
    add_test_medicine(client, stock=20, price=10)
    client.post("/add", data={
        "name": "Paracetamol",
        "price": "12",
        "stock": "5"
    })
    assert pharmacy.medicines["Paracetamol"]["price"] == 12.00
    assert pharmacy.medicines["Paracetamol"]["stock"] == 25


def test_generate_bill_calculates_total_and_reduces_stock(client):
    add_test_medicine(client, stock=20, price=10)

    response = client.post("/bill", data={
        "name": "Paracetamol",
        "quantity": "3"
    })

    assert response.status_code == 200
    assert b"Pharmacy Bill" in response.data
    assert b"30.00" in response.data
    assert pharmacy.medicines["Paracetamol"]["stock"] == 17
    assert len(pharmacy.bills) == 1


def test_billing_rejects_insufficient_stock(client):
    add_test_medicine(client, stock=2)

    response = client.post("/bill", data={
        "name": "Paracetamol",
        "quantity": "3"
    })

    assert response.status_code == 400
    assert pharmacy.medicines["Paracetamol"]["stock"] == 2
    assert len(pharmacy.bills) == 0


def test_billing_rejects_unknown_medicine(client):
    response = client.post("/bill", data={
        "name": "Unknown",
        "quantity": "1"
    })
    assert response.status_code == 400


@pytest.mark.parametrize("quantity", ["0", "-1", "abc"])
def test_billing_rejects_invalid_quantity(client, quantity):
    add_test_medicine(client)

    response = client.post("/bill", data={
        "name": "Paracetamol",
        "quantity": quantity
    })

    assert response.status_code == 400
    assert pharmacy.medicines["Paracetamol"]["stock"] == 20
    assert len(pharmacy.bills) == 0


@pytest.mark.parametrize("data", [
    {"name": "", "price": "10", "stock": "5"},
    {"name": "Paracetamol", "price": "0", "stock": "5"},
    {"name": "Paracetamol", "price": "10", "stock": "-1"},
    {"name": "Paracetamol", "price": "abc", "stock": "5"},
])
def test_invalid_medicine_is_rejected(client, data):
    response = client.post("/add", data=data)
    assert response.status_code == 400


def test_view_bill_history_is_not_available_in_v2(client):
    response = client.get("/bills/1")
    assert response.status_code == 404
