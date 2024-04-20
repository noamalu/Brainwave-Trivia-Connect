from asyncio import timeout
import logging
import socket
import struct
import threading
import sys
import time
import random
from enum import Enum

from clientApp import Client
from config import *

class MessageTypes(Enum):
    RECEIVED = 1
    TIMEOUT = 2
    CONNECTION_CLOSED = 3
    ERROR = 4

class Bot(Client):
    def __init__(self, portListen):
        self.portListen = portListen
        self.TCP_Socket = None
        self.done = False
        self.name = "BOT: OpenAI"

        self.colors = {
            MessageTypes.RECEIVED: '\033[48;5;15m',  # Light Pink
            MessageTypes.TIMEOUT: '\033[48;5;33m',   # Blue
            MessageTypes.CONNECTION_CLOSED: '\033[48;5;196m',  # Red
            MessageTypes.ERROR: '\033[48;5;214m'  # Yellow
        }

    def print_colored_message(self, message_type, message):
        color_code = self.colors.get(message_type, '')
        print(color_code + message)

    def receive_message_from_server(self):
        # Receives messages from the server.
        while not self.done:
            try:
                data = self.TCP_Socket.recv(SOCKET_BUFFER_SIZE)
                # Check if socket is closed
                if not data:
                    raise ConnectionError
                logging.info("Received: " + data.decode('utf-8'))
                data = data.decode('utf-8')
                self.print_colored_message(MessageTypes.RECEIVED, data)
                with self.condition:
                    self.condition.notify_all()
            except socket.timeout:
                self.print_colored_message(MessageTypes.TIMEOUT, "Socket timeout occurred")
                continue
            except (ConnectionError, ConnectionResetError):
                self.print_colored_message(MessageTypes.CONNECTION_CLOSED, "Connection closed")
                if not self.done:
                    self.done = True
                    with self.condition:
                        self.condition.notify_all()
                break

    def send_data_to_server(self):
        # Sends data to the server.
        firstMsg = True
        while not self.done:
            try:
                # Input timeout for 5 seconds
                if firstMsg:
                    message = self.name
                    firstMsg = False
                else:
                    message = random.choice(["Y", "N"])

                self.TCP_Socket.send(message.encode())
                logging.info("Sent: " + message)
                self.print_colored_message(random.choice(list(self.colors.keys())), "Sent: " + message)
                with self.condition:
                    self.condition.wait()
                time.sleep(1)
            except ConnectionError:
                self.print_colored_message(MessageTypes.CONNECTION_CLOSED, "Connection closed")
                self.done = True
                break

    def main_loop(self):
        try:
            self.TCP_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.host = HOST

            self.TCP_Socket.connect((self.host.strip(), self.portListen))

            self.done = False
            self.condition = threading.Condition()
            receive_thread = threading.Thread(target=self.receive_message_from_server)
            send_thread = threading.Thread(target=self.send_data_to_server)
            receive_thread.start()
            send_thread.start()
            receive_thread.join()
            send_thread.join()
        except Exception as e:
            self.print_colored_message(MessageTypes.ERROR, "An error occurred: " + str(e))
        finally:
            if self.TCP_Socket:
                self.TCP_Socket.close()

if __name__ == "__main__":
    bot = Bot(PORT)
    bot.main_loop()
