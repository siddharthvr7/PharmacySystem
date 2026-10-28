
import pytest
import app as pharmacy


@pytest.fixture(autouse=True)
def reset_data():
    with pharmacy.data_lock:
        pharmacy.medicines.clear()
        pharmacy.bills.clear()
        pharmacy.next_bill_id = 1

    yield

    with pharmacy.data_lock:
        pharmacy.medicines.clear()
        pharmacy.bills.clear()
        pharmacy.next_bill_id = 1


@pytest.fixture
def client():
    pharmacy.app.config["TESTING"] = True
    with pharmacy.app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["version"] == "v3"


def test_add_medicine(client):
    response = client.post("/add", data={
        "name": "Paracetamol",
        "price": "10",
        "stock": "20"
    })

    assert response.status_code == 302
    assert pharmacy.medicines["Paracetamol"]["stock"] == 20


def test_generate_bill(client):
    client.post("/add", data={
        "name": "Paracetamol",
        "price": "10",
        "stock": "20"
    })

    response = client.post("/bill", data={
        "name": "Paracetamol",
        "quantity": "3"
    })

    assert response.status_code == 302
    assert pharmacy.bills[0]["total"] == 30.00
    assert pharmacy.medicines["Paracetamol"]["stock"] == 17


def test_reject_insufficient_stock(client):
    client.post("/add", data={
        "name": "Paracetamol",
        "price": "10",
        "stock": "2"
    })

    response = client.post("/bill", data={
        "name": "Paracetamol",
        "quantity": "5"
    })

    assert response.status_code == 400
    assert pharmacy.medicines["Paracetamol"]["stock"] == 2


def test_view_bill(client):
    client.post("/add", data={
        "name": "Paracetamol",
        "price": "10",
        "stock": "20"
    })
    client.post("/bill", data={
        "name": "Paracetamol",
        "quantity": "2"
    })

    response = client.get("/bills/1")
    assert response.status_code == 200
    assert b"Pharmacy Bill" in response.data


def test_unknown_bill(client):
    response = client.get("/bills/999")
    assert response.status_code == 404
