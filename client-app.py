import socket
import struct
import threading
import sys

class Client:
    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.name = ""
        self.tcp_socket = None
        
    def receive_msg_from_server(self):
        """Continuously listen for messages from the server and handle them. 
        Do not prompt for user input on the first message."""
        
        while True:
            try:
                data = self.tcp_socket.recv(1024).decode("utf-8")
                print(data)
                
                # Check if the message indicates disqualification
                if "disqualified" in data.lower():
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

    def broadcasts_catcher(self):
        """Listen for UDP broadcast messages to discover servers."""
        try:
            UDP_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            UDP_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            UDP_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            UDP_SOCKET.bind(('', self.port))
            print("Listening for server offers...")

            while True:
                data, addr = UDP_SOCKET.recvfrom(1024)
                magic_cookie, message_type, server_name, server_port = struct.unpack('!Ib32sH', data)
                if magic_cookie == 0xabcddcba and message_type == 0x2:
                    server_name = server_name.decode().rstrip('\x00')  # Remove null characters from the end
                    print(f"Received offer from server: {server_name} at {addr[0]}:{server_port}")
                    return addr[0], server_port  # Return server IP and port
        except Exception as e:
            print(f"Error listening for server offers: {e}")
            return None, None

    def connect_to_server(self):
        """Establish connection to the server."""
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.host, self.port))
            print("Connected to the server.")
            self.name = input("Enter your name:\n")
            self.tcp_socket.sendall(self.name.encode())
        except Exception as e:
            print(f"Could not connect to the server: {e}")
            return None

def main():
    # Listen for server offers
    host = "10.0.0.9"
    port = 13117
    client = Client(host, port)
    if not client:
        print("No server offers received. Exiting.")
        return

    # Connect to the server
    client.connect_to_server()
    
    # After connecting, start listening for messages (questions) from the server
    client.receive_msg_from_server()

if __name__ == "__main__":
    main()