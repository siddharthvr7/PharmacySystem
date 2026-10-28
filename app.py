
from flask import Flask, render_template, request, redirect, url_for, abort
from threading import Lock

app = Flask(__name__)

# Version 1: data is stored in memory.
medicines = {}
bills = []
next_bill_id = 1
data_lock = Lock()


@app.route("/")
def index():
    with data_lock:
        medicine_list = {
            name: item.copy() for name, item in medicines.items()
        }
        bill_list = [item.copy() for item in bills]

    return render_template(
        "index.html",
        medicines=medicine_list,
        bills=bill_list
    )


@app.route("/add", methods=["POST"])
def add_medicine():
    name = request.form.get("name", "").strip()

    try:
        price = float(request.form.get("price", ""))
        stock = int(request.form.get("stock", ""))
    except (ValueError, TypeError):
        abort(400, description="Invalid price or stock.")

    if not name or price <= 0 or stock < 0:
        abort(400, description="Enter a valid name, price and stock.")

    with data_lock:
        if name in medicines:
            medicines[name]["price"] = round(price, 2)
            medicines[name]["stock"] += stock
        else:
            medicines[name] = {
                "price": round(price, 2),
                "stock": stock
            }

    return redirect(url_for("index"))


@app.route("/bill", methods=["POST"])
def generate_bill():
    global next_bill_id

    name = request.form.get("name", "").strip()

    try:
        quantity = int(request.form.get("quantity", ""))
    except (ValueError, TypeError):
        abort(400, description="Invalid quantity.")

    if quantity <= 0:
        abort(400, description="Quantity must be positive.")

    with data_lock:
        if name not in medicines:
            abort(400, description="Medicine not found.")

        medicine = medicines[name]

        if quantity > medicine["stock"]:
            abort(400, description="Insufficient stock.")

        total = round(medicine["price"] * quantity, 2)
        medicine["stock"] -= quantity

        bill = {
            "id": next_bill_id,
            "medicine": name,
            "quantity": quantity,
            "unit_price": medicine["price"],
            "total": total
        }

        bills.append(bill)
        next_bill_id += 1
        bill_id = bill["id"]

    return redirect(url_for("view_bill", bill_id=bill_id))


@app.route("/bills/<int:bill_id>")
def view_bill(bill_id):
    with data_lock:
        bill = next(
            (item.copy() for item in bills if item["id"] == bill_id),
            None
        )

    if bill is None:
        abort(404)

    return render_template("bill.html", bill=bill)


@app.route("/health")
def health():
    return {"status": "healthy", "version": "v3"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
