import html
import socket
import struct
import threading
import time
from datetime import datetime, timedelta
import requests

def get_trivia_questions(QuestionsAmount, typeOfAnswers):
    # URL of the API
    url = f"https://opentdb.com/api.php?amount={QuestionsAmount}&type={typeOfAnswers}"

    # Send a GET request to the API
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # If successful, return the response content
        return response.json()
    else:
        # If not successful, print an error message and return None
        print("Failed to retrieve data from the API:", response.status_code)
        return None

def print_question(question_data):
    print("Question:", question_data['question'])
    print("Correct Answer:", question_data['correct_answer'])
    print("Incorrect Answers:")
    for answer in question_data['incorrect_answers']:
        print("-", answer)
    print()

def parse_questions_response(response):
    parsed_questions = []
    results = response.get('results', [])
    
    for result in results:
        parsed_question = {
            'question': html.unescape(result.get('question', '')),
            'correct_answer': html.unescape(result.get('correct_answer', '')),
            'incorrect_answers': [html.unescape(answer) for answer in result.get('incorrect_answers', [])]
        }
        parsed_questions.append(parsed_question)
    
    return parsed_questions
        

def fetch_and_parse_questions(QuestionsAmount, typeOfAnswers):
    unparsedData = get_trivia_questions(QuestionsAmount, typeOfAnswers)
    return parse_questions_response(unparsedData)    

connections = []
total_connections = 0
game_started = False

class Client(threading.Thread):
    def __init__(self, socket, address, id, signal):
        threading.Thread.__init__(self)
        self.socket = socket
        self.address = address
        self.id = id
        self.name = ""
        self.signal = signal
        self.first_message_received = False  # connect msg

    
    def __str__(self):
        return f"Client {self.id} {self.name} from {str(self.address)}"

def accept_clients(sock):
    global game_started
    while not game_started:
        try:
            client_socket, address = sock.accept()
            global total_connections
            new_client = Client(client_socket, address, total_connections, True)
            new_client.name = new_client.socket.recv(1024).decode().strip()
            connections.append(new_client)
            print(f"New connection: {new_client.name}")
            total_connections += 1
        except socket.timeout:
            # If no new connections within a certain time, break the loop
            break
    print("No longer accepting new clients. Game is starting.")

def receive(client):
    try:
        while client.signal:
            if not client.first_message_received:
                # Skip the first message (name of the client, already handled during connection)
                client.first_message_received = True
                continue
            
            data = client.socket.recv(1024).decode().strip()
            if data:
                print(f"Client {client.name} answered {data}")
                # Here, you could add logic to check answers, update scores, etc.
    except Exception as e:
        print(f"Error receiving data from client {client.name}: {e}")
    finally:
        client.socket.close()
        connections.remove(client)

def send_to_clients(message):
    for client in connections:
        try:
            client.socket.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message to {client.address}: {e}")

def broadcast_offers():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message = struct.pack('!IbH', 0xabcddcba, 0x2, 13117)
    while not game_started:
        udp_socket.sendto(message, ('<broadcast>', 13117))
        time.sleep(1)

def main():
    global game_started
    host = '0.0.0.0'
    port = 13117

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(5)
    sock.settimeout(5)  # Set a timeout for accepting connections
    print(f"Server started, listening on IP address {host}")

    threading.Thread(target=broadcast_offers, args=()).start()

    accept_clients(sock)

    game_started = True  # Stop accepting new clients and start the game

    # Game logic (fetch questions, send them to clients, receive answers, etc.)
    # Example: send_to_clients("Welcome to the trivia game!")

    # Example game loop (simplified)
    questions = fetch_and_parse_questions(5, "boolean")
    for question in questions:
        current_question = question['question']
        send_to_clients(current_question)
        for client in connections:
            threading.Thread(target=receive, args=(client,)).start()

    # Cleanup and closing connections can go here

if __name__ == "__main__":
    main()