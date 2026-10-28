
from flask import Flask, render_template, request, redirect, url_for, abort
from threading import Lock

app = Flask(__name__)

# Version 1: Add Items only. Data is stored in memory.
medicines = {}
data_lock = Lock()


@app.route("/")
def index():
    with data_lock:
        medicine_list = {
            name: item.copy() for name, item in medicines.items()
        }

    return render_template("index.html", medicines=medicine_list)


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


@app.route("/health")
def health():
    return {"status": "healthy", "version": "v1"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
