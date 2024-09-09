import socket
import json

IP = socket.gethostbyname("ccscloud.dlsu.edu.ph")  # server IP
PORT = 20281  # server port
ADDR = (IP, PORT)
SIZE = 5024
FORMAT = "utf-8"
DISCONNECT_MSG = "!DISCONNECT"
TERMINAL_ID = "Terminal_1"  # Example terminal ID

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print(f"Attempting to connect to server at {IP}:{PORT}")
        client.connect(ADDR)
        print(f"[CONNECTED] Client connected to server at {IP}:{PORT}\n")

        registered = False
        print("Welcome! Please scan RFID to register.\n")

        while True:
            
            response = client.recv(SIZE).decode(FORMAT)


            try:
                response_data = json.loads(response)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                continue
            
            message = response_data.get("message", "")
            print(f"Processed message: {message}")

            if "registered successfully" in message:
                print("RFID registered. Enjoy your free 500 pesos.\n")
                registered = True
            elif "Transaction successful" in message:
                balance = response_data.get("remaining_balance", 0)
                print(f"Transaction Complete!\nRemaining balance: {balance}\n")
            elif "Insufficient balance" in message:
                print("Insufficient balance. Please top up your account.\n")
            elif "Invalid RFID" in message:
                print("RFID not registered. Please try again.\n")
            
            if registered:
                print("Please scan RFID to enter.\n")
            else:
                print("Welcome! Please scan RFID to register.\n")
                    

    except Exception as e:
        print(f"Failed to connect to server: {e}")

if __name__ == "__main__":
    main()
