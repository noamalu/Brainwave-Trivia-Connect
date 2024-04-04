import socket
import struct
import threading
import sys

def receive_msg_from_server(tcp_socket):
    """Continuously listen for messages from the server and handle them. 
    Do not prompt for user input on the first message."""
    first_message = True  # Flag to track if it's the first message received
    while True:
        try:
            data = tcp_socket.recv(1024).decode("utf-8")
            if data:
                if first_message:
                    # Handle the first message (e.g., game start message) without prompting for input
                    print(data)
                    first_message = False  # Update the flag after the first message is processed
                else:
                    # For subsequent messages, prompt the user for their answer
                    print(f"Question: {data}")
                    answer = input("Your answer: ")
                    send_msg_to_server(tcp_socket, answer)
        except Exception as e:
            print(f"Error receiving message: {e}")
            break


def send_msg_to_server(tcp_socket, message):
    """Send a message (user's answer) to the server."""
    try:
        tcp_socket.sendall(message.encode())
    except Exception as e:
        print(f"Error sending message: {e}")

def connect_to_server(host, port):
    """Establish connection to the server."""
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((host, port))
        print("Connected to the server. Waiting for the game to start...")
        name = input("Enter your name:\n")
        tcp_socket.sendall(name.encode())

        return tcp_socket
    except Exception as e:
        print(f"Could not connect to the server: {e}")
        sys.exit(0)

def main():
    host = 'localhost' # Server host (IP address or hostname)
    port = 13117         # Server port for the trivia game

    tcp_socket = connect_to_server(host, port)
    
    # After connecting, start listening for messages (questions) from the server
    receive_msg_from_server(tcp_socket)

if __name__ == "__main__":
    main()
