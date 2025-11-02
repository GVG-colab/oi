import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import socketio
import json
import os

SERVER_URL = "https://SEUSERVIDOR.onrender.com"  # troca pelo domínio que Render dá

sio = socketio.Client()
HISTORY_DIR = "historico"

# ==== Histórico local ====
def save_message_local(room, sender, text):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    filename = os.path.join(HISTORY_DIR, f"{room}.json")
    data = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
    data.append({"sender": sender, "message": text})
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def load_history(room):
    filename = os.path.join(HISTORY_DIR, f"{room}.json")
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as f:
        return json.load(f)

# ==== Tkinter ====
root = tk.Tk()
root.title("Chat Tkinter + SocketIO")

chat_box = scrolledtext.ScrolledText(root, state="disabled", width=60, height=20)
chat_box.pack(padx=10, pady=10)

entry_msg = tk.Entry(root, width=50)
entry_msg.pack(side=tk.LEFT, padx=(10,0), pady=(0,10))
entry_msg.focus()

btn_send = tk.Button(root, text="Enviar")
btn_send.pack(side=tk.LEFT, padx=10, pady=(0,10))

# ===== Login / Registo =====
import requests

choice = messagebox.askquestion("Conta", "Já tens conta?")

if choice == "no":
    username = simpledialog.askstring("Registo", "Nome de utilizador:")
    password = simpledialog.askstring("Registo", "Senha:", show="*")
    r = requests.post(f"{SERVER_URL}/register", json={"username": username, "password": password})
    if r.status_code == 200:
        number = r.json()["number"]
        messagebox.showinfo("Conta criada", f"O teu número é: {number}")
    else:
        messagebox.showerror("Erro", "Falha no registo")
        exit()
else:
    number = simpledialog.askstring("Login", "Número:")
    password = simpledialog.askstring("Login", "Senha:", show="*")
    r = requests.post(f"{SERVER_URL}/login", json={"number": number, "password": password})
    if r.status_code == 200:
        username = r.json()["username"]
    else:
        messagebox.showerror("Erro", "Falha no login")
        exit()

# ===== Sala de chat =====
room = simpledialog.askstring("Sala", "Com quem queres conversar? (põe o número do contacto)")

@sio.event
def connect():
    sio.emit("join", {"room": room})
    # Carrega histórico local
    for msg in load_history(room):
        chat_box.config(state="normal")
        chat_box.insert(tk.END, f"{msg['sender']}: {msg['message']}\n")
        chat_box.config(state="disabled")

@sio.on("receive_message")
def on_message(data):
    chat_box.config(state="normal")
    chat_box.insert(tk.END, f"{data['sender']}: {data['message']}\n")
    chat_box.config(state="disabled")
    save_message_local(room, data['sender'], data['message'])

def send_message(event=None):
    text = entry_msg.get().strip()
    if not text:
        return
    entry_msg.delete(0, tk.END)
    chat_box.config(state="normal")
    chat_box.insert(tk.END, f"Tu: {text}\n")
    chat_box.config(state="disabled")
    save_message_local(room, "Tu", text)
    sio.emit("send_message", {"room": room, "message": text, "sender": number})

btn_send.config(command=send_message)
entry_msg.bind("<Return>", send_message)

sio.connect(SERVER_URL)
root.mainloop()
