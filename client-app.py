import socket
import struct
import threading
import sys

#Wait for incoming data from server
#.decode is used to turn the message in bytes to a string
name = "temp name"

def receive(socket, signal):
    while not signal:
        try:
            data = socket.recv(1024)
            print(str(data.decode("utf-8")))
        except:
            print("You have been disconnected from the server")
            signal = False
            break

def listen_for_offers():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR , 1)
    udp_socket.bind(('', 13117))
    print("Client started, listening for offer requests...")
    while True:
        data, addr = udp_socket.recvfrom(1024)
        magic_cookie, message_type, server_port = struct.unpack('!IbH', data)
        if (magic_cookie == 0xabcddcba and message_type == 0x2):
            print(f"Received offer from {addr[0]}, attempting to connect...")
            connect_to_server(addr[0], server_port)
            break

def connect_to_server(host, port):
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((host, port))
        print("Connected to the server.")
        name = input("Enter your name:\n")
        tcp_socket.sendall(name.encode())

        receive_thread = threading.Thread(target=receive, args=(tcp_socket,False))
        receive_thread.start()
        while True:
            message = input()
            if message:
                tcp_socket.sendall(message.encode())
    except Exception as e:
        print(f"Could not connect to the server: {e}")
        sys.exit(0)


if __name__ == "__main__":
    listen_for_offers()








# #Get host and port
# host = input("Host: ")
# port = int(input("Port: "))

# #Attempt connection to server
# try:
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.connect((host, port))
# except:
#     print("Could not make a connection to the server")
#     input("Press enter to quit")
#     sys.exit(0)

# #Create new thread to wait for data
# receiveThread = threading.Thread(target = receive, args = (sock, True))
# receiveThread.start()

# #Send data to server
# #str.encode is used to turn the string message into bytes so it can be sent across the network
# while True:
#     message = input()
#     sock.sendall(str.encode(message))
    