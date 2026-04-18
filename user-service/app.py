from flask import Flask, jsonify, request
import time, os, uuid

app = Flask(__name__)
VERSION = os.environ.get("APP_VERSION", "1.0.0")
START_TIME = time.time()
USERS = {}

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "version": VERSION,
                    "uptime": round(time.time() - START_TIME, 2)})

@app.route("/api/users", methods=["GET"])
def list_users():
    return jsonify({"users": list(USERS.values()), "count": len(USERS), "version": VERSION})

@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.get_json() or {}
    uid = str(uuid.uuid4())[:8]
    user = {"id": uid, "name": data.get("name", "unknown"), "email": data.get("email", "")}
    USERS[uid] = user
    return jsonify(user), 201

@app.route("/api/users/<uid>", methods=["GET"])
def get_user(uid):
    if uid not in USERS:
        return jsonify({"error": "not found"}), 404
    return jsonify(USERS[uid])

@app.route("/api/users/<uid>", methods=["DELETE"])
def delete_user(uid):
    if uid not in USERS:
        return jsonify({"error": "not found"}), 404
    del USERS[uid]
    return jsonify({"deleted": uid})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
