import random
import socket
import struct
import threading
import sys
import time

from config import *

class Client(ColoredPrinter):
    def __init__(self,host,port):
        super().__init__()
        self.host = host
        self.port = port
        self.name = random.choice(NAME_BANK)
        self.tcp_socket = None
        self.UDP_SOCKET = None

    def receive_msg_from_server(self):
        """Continuously listen for messages from the server and handle them."""
        while True:
            try:
                self.tcp_socket.settimeout(SOCKET_TIMEOUT+SAFTY_FIRST)
                data = self.tcp_socket.recv(SOCKET_BUFFER_SIZE).decode("utf-8")
                self.print(data)
                if not data:
                    break  # Exit the loop if disqualified

                # If the message indicates that the user should input their answer
                if "True or False:" in data:
                    # Prompt the user for their answer
                    answer = input("Your answer: ")
                    self.send_msg_to_server(answer)
            except Exception as e:
                self.print(f"Connection closed")
                self.tcp_socket.close()
                break


    def send_msg_to_server(self, message):
        """Send a message (user's answer) to the server."""
        try:
            self.tcp_socket.sendall(message.encode())
        except Exception as e:
            self.print(f"Error sending message: {e}")

    def connect_to_server(self):
        """Establish connection to the server."""
        self.print("Client started, listening for offer requests...")
        self.tcp_socket = None
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if(self.tcp_socket):
                self.print(f"Received offer from server at address {self.host}, attempting to connect...")
                self.tcp_socket.connect((self.host, self.port))
                self.tcp_socket.sendall(self.name.encode())
                return True
        except Exception as e:
            self.print(f"Could not connect to the server: {e}")
            return False

def get_local_ip_address():
    return socket.gethostbyname(socket.gethostname())

def main():
    # Listen for server offers
    host = get_local_ip_address()
    if host is None:
        print("No suitable IP address found.")
        return
    
    port = PORT
    
    client = Client(host, port)
    while True:
        if not client.connect_to_server():
            client.print("No server offers received or could not connect. Retrying in 3 seconds...")
            time.sleep(1)
            continue

        # Start listening for messages (questions) from the server
        client.receive_msg_from_server()

        # Server disconnected, attempt to reconnect
        client.print("Server disconnected. Reconnecting...")
        client.tcp_socket.close()
        client = Client(host, port)

if __name__ == "__main__":
    main()