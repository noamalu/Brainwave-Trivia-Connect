import socket
import struct
import threading
import sys
import time

class Client:
    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.name = ""
        self.tcp_socket = None
        self.UDP_SOCKET = None

    def receive_msg_from_server(self):
        """Continuously listen for messages from the server and handle them. 
        Do not prompt for user input on the first message."""
        
        while True:
            try:
                data = self.tcp_socket.recv(1024).decode("utf-8")
                print(data)
                
                # Check if the message indicates disqualification
                if not data:
                    break  # Exit the loop if disqualified
                    
                # For subsequent messages, prompt the user for their answer
                answer = input("Your answer: ")
                self.send_msg_to_server(answer)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break


    def send_msg_to_server(self, message):
        """Send a message (user's answer) to the server."""
        try:
            self.tcp_socket.sendall(message.encode())
        except Exception as e:
            print(f"Error sending message: {e}")

    def connect_to_server(self):
        """Establish connection to the server."""
        print("Client started, listening for offer requests...")
        self.tcp_socket = None
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if(self.tcp_socket):
                print(f"Received offer from server “Mystic” at address {self.host}, attempting to connect...")
                self.tcp_socket.connect((self.host, self.port))
                self.name = input("Enter your name:\n")
                self.tcp_socket.sendall(self.name.encode())
                return True
        except Exception as e:
            print(f"Could not connect to the server: {e}")
            return False


def main():
    # Listen for server offers
    host = "10.100.102.47"

    port = 13117
    client = Client(host, port)
    if not client:
        print("No server offers received. Exiting.")
        return

    # Connect to the server
    # After connecting, start listening for messages (questions) from the server
    client.connect_to_server()
    client.receive_msg_from_server()

    # disconnecting from server
    print("Server disconnected, listening for offer requests...")

    client.tcp_socket.close()
    while True:
        if  client.connect_to_server() == False or client.tcp_socket == None:
            time.sleep(3)
        else: #TODO: adjust dup code
            client.receive_msg_from_server()
            #print("Server disconnected, listening for offer requests...")
            #client.tcp_socket.close()



if __name__ == "__main__":
    main()