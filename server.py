from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import uuid

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# Registro de utilizador
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    number = str(uuid.uuid4())[:8]
    users = load_json(USERS_FILE)
    users[number] = {"username": data["username"], "password": data["password"]}
    save_json(USERS_FILE, users)
    return {"number": number}, 200

# Login de utilizador
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    users = load_json(USERS_FILE)
    for number, info in users.items():
        if number == data["number"] and info["password"] == data["password"]:
            return {"username": info["username"]}, 200
    return {"error": "Login falhou"}, 401

# SocketIO para mensagens
@socketio.on("join")
def handle_join(data):
    room = data["room"]
    join_room(room)

@socketio.on("leave")
def handle_leave(data):
    room = data["room"]
    leave_room(room)

@socketio.on("send_message")
def handle_message(data):
    room = data["room"]
    message = data["message"]
    sender = data["sender"]

    # Guarda no histórico do servidor
    messages = load_json(MESSAGES_FILE)
    if room not in messages:
        messages[room] = []
    messages[room].append({"sender": sender, "message": message})
    save_json(MESSAGES_FILE, messages)

    emit("receive_message", {"sender": sender, "message": message}, room=room)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
