import logging
import socket
import struct
import threading
import sys
import time
import random
from enum import Enum
from clientApp import Client  # Assuming this is where your Client class is defined
from config import *

class Bot(Client):
    def __init__(self, host, port):
        super().__init__(host, port)
        self.name = f"BOT: {random.choice(NAME_BANK)}"

    def receive_message_from_server(self):
        # Receives messages from the server.
        while not self.done:
            try:
                data = self.tcp_socket.recv(SOCKET_BUFFER_SIZE)
                # Check if socket is closed
                if not data:
                    raise ConnectionError
                data = data.decode('utf-8')
                self.print(data)
                with self.condition:
                    self.condition.notify_all()
            except (ConnectionError, ConnectionResetError):
                self.print("Connection closed")
                if not self.done:
                    self.done = True
                    with self.condition:
                        self.condition.notify_all()
                break

    def send_to_server(self):
        firstMsg = True
        while not self.done:
            try:
                if firstMsg:
                    msg = self.name
                    firstMsg = False
                else:
                    msg = random.choice(["I Don't Know :("] + list(RESPONSE_MAP.keys()))
                self.tcp_socket.send(msg.encode())
                self.print(msg)
                with self.condition:
                    self.condition.wait()
                time.sleep(1)
            except ConnectionError:
                self.print("Connection closed")
                self.done = True
                break

    def start(self):
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.host, self.port))

            self.done = False
            self.condition = threading.Condition()
            outgoing = threading.Thread(target=self.send_to_server)
            incoming = threading.Thread(target=self.receive_message_from_server)
            incoming.start()
            outgoing.start()
            incoming.join()
            outgoing.join()
        except Exception as e:
            self.print("An error occurred: " + str(e))
        finally:
            if self.tcp_socket:
                self.tcp_socket.close()

def get_local_ip_address():
    return socket.gethostbyname(socket.gethostname())

if __name__ == "__main__":
    host = get_local_ip_address()
    if host is None:
        print("No suitable IP address found.")
    bot = Bot(host, PORT)
    bot.start()
