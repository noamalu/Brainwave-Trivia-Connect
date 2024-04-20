from asyncio import timeout
import logging
import socket
import struct
import threading
import sys
import time
import random

from clientApp import Client

class Bot(Client):
    def __init__(self, portListen):
        self.portListen = portListen
        self.TCP_Socket = None
        self.done = False
        self.name = "BOT: OpenAI"

        self.colors = ['\033[91m', '\033[92m', '\033[93m', '\033[94m', '\033[95m', '\033[96m', '\033[97m']

    def receive_message_from_server(self):
        # Receives messages from the server.
        while not self.done:
            try:
                data = self.TCP_Socket.recv(1024)
                # Check if socket is closed
                if not data:
                    raise ConnectionError
                logging.info("Received: " + data.decode('utf-8'))
                data = data.decode('utf-8')
                print("\x1b[48;5;15m", data)  # Light Pink for received messages
                with self.condition:
                    self.condition.notify_all()
            except socket.timeout:
                print("\x1b[48;5;15mSocket timeout occurred")  # Blue for timeout messages
                continue
            except ConnectionError or ConnectionResetError:
                print("\x1b[48;5;15mConnection closed")  # Red for connection closed messages
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
                print(random.choice(self.colors) + "Sent: " + message)
                with self.condition:
                    self.condition.wait()
                time.sleep(1)
            except ConnectionError:
                print(random.choice(self.colors) + "Connection closed")
                self.done = True
                break

    def main_loop(self):
        # Main loop of the bot.
        try:
            self.TCP_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.TCP_Socket.settimeout(5)  # Timeout for socket operations
            self.host = '10.100.102.47'
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
            print(random.choice(self.colors) + "An error occurred:", e)
        finally:
            if self.TCP_Socket:
                self.TCP_Socket.close()

if __name__ == "__main__":
    bot = Bot(13117)
    bot.main_loop()

