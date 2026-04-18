from flask import Flask, jsonify, request
import time, os, uuid

app = Flask(__name__)
VERSION = os.environ.get("APP_VERSION", "1.0.0")
START_TIME = time.time()
PRODUCTS = {}

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "version": VERSION,
                    "uptime": round(time.time() - START_TIME, 2)})

@app.route("/api/products", methods=["GET"])
def list_products():
    category = request.args.get("category")
    items = list(PRODUCTS.values())
    if category:
        items = [p for p in items if p.get("category") == category]
    return jsonify({"products": items, "count": len(items), "version": VERSION})

@app.route("/api/products", methods=["POST"])
def create_product():
    data = request.get_json() or {}
    pid = str(uuid.uuid4())[:8]
    product = {"id": pid, "name": data.get("name", "unnamed"),
                "price": data.get("price", 0.0),
                "category": data.get("category", "general"),
                "stock": data.get("stock", 0)}
    PRODUCTS[pid] = product
    return jsonify(product), 201

@app.route("/api/products/<pid>", methods=["GET"])
def get_product(pid):
    if pid not in PRODUCTS:
        return jsonify({"error": "not found"}), 404
    return jsonify(PRODUCTS[pid])

@app.route("/api/products/<pid>", methods=["PUT"])
def update_product(pid):
    if pid not in PRODUCTS:
        return jsonify({"error": "not found"}), 404
    data = request.get_json() or {}
    PRODUCTS[pid].update({k: v for k, v in data.items() if k != "id"})
    return jsonify(PRODUCTS[pid])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
