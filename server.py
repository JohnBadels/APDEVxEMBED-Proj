import socket
import threading
import json
from datetime import datetime
import csv
import os
from threading import Lock

IP = '10.2.201.204'
PORT = 8000
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
DISCONNECT_MSG = "!DISCONNECT"

registered_rfid = None  # This will hold the first RFID that is registered
balance = 0  # Initial balance for the registered RFID
transactions = []  # List to hold transaction records

mx = Lock()

CLIENTS = {}

def write_to_csv(log_entry):
    file_exists = os.path.isfile('output.csv')

    with open('output.csv', mode='a', newline='') as csvfile:
        fieldnames = log_entry.keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(log_entry)

def handle_client(conn, addr):
    global registered_rfid, balance
    print(f"\n[NEW CONNECTION] {addr} connected.\n")
    
    pingOnce = False
    connected = True
    while connected:
        try:
            msg = conn.recv(SIZE).decode(FORMAT)
            if not msg:
                continue
            
            # Simple ping
            if pingOnce != True:
                conn.send(b'Hello world!')
            
            print(f"Raw message received: {msg}")  # Debugging statement
            
            try:
                data = json.loads(msg)  # Expecting JSON data
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                continue

            rfid_uid = data['rfid_uid']
            terminal_id = data['terminal_id']
            timestamp = data['timestamp']
            t = data["type"]

            print(f"Received from client:\nUID: {rfid_uid}\nType: {t}\nTerminal: {terminal_id}\nDate/Time: {timestamp}\n")
            write_to_csv(data)

            response = {}
            if registered_rfid is None:
                registered_rfid = rfid_uid
                balance = 500  # Set initial balance
                response = {
                    "message": f"RFID UID: {rfid_uid} registered successfully with balance 500."
                }
            else:
                if rfid_uid == registered_rfid:
                    if balance >= 35:
                        balance -= 35
                        response = {
                            "message": "Transaction successful.",
                            "remaining_balance": balance
                        }
                        transactions.append((rfid_uid, terminal_id, timestamp, "Success", balance))
                    else:
                        response = {
                            "message": "Insufficient balance. Please top up your account."
                        }
                        transactions.append((rfid_uid, terminal_id, timestamp, "Insufficient Balance", balance))
                else:
                    response = {
                        "message": "Invalid RFID."
                    }
                    transactions.append((rfid_uid, terminal_id, timestamp, "Invalid RFID", balance))

            print(f"Response to client:\n{json.dumps(response, indent=4)}\n")
            print("-" * 34 + "\n")
            tosend = json.dumps(response).encode(FORMAT)
            
            for client in CLIENTS.values():
                client.send(tosend)

        except Exception as e:
            print(f"Error: {e}")
            connected = False

    conn.close()

def main():
    print("[STARTING] Server is starting...\n")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print(f"[LISTENING] Server is listening on {IP}:{PORT}\n")

    while True:
        conn, addr = server.accept()
        CLIENTS[conn.fileno()] = conn
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}\n")

if __name__ == "__main__":
    main()
