from concurrent.futures import ThreadPoolExecutor
import html
import logging
import socket
import struct
import threading
import time
from datetime import datetime, timedelta
import requests

from config import *

trivia_questions = [
    {"question": "ASGI stands for Asynchronous Server Gateway Interface.", IS_TRUE: True},
    {"question": "ASGI is a Python specification for building asynchronous web applications.", IS_TRUE: True},
    {"question": "ASGI was developed as an evolution of WSGI to support asynchronous programming in web servers.", IS_TRUE: True},
    {"question": "ASGI allows web applications to handle long-lived connections efficiently.", IS_TRUE: True},
    {"question": "ASGI servers can handle protocols like HTTP, WebSockets, and others.", IS_TRUE: True},
    {"question": "ASGI applications are typically run using an ASGI server like Daphne or uvicorn.", IS_TRUE: True},
    {"question": "ASGI is primarily used in Python frameworks like Django Channels and Starlette.", IS_TRUE: True},
    {"question": "ASGI supports both synchronous and asynchronous handlers.", IS_TRUE: True},
    {"question": "ASGI was introduced in Python 3.5 as a standard for asynchronous web servers.", IS_TRUE: False},
    {"question": "ASGI stands for Asynchronous Gateway Interface.", IS_TRUE: False},
    {"question": "ASGI applications cannot handle WebSocket connections.", IS_TRUE: False},
    {"question": "ASGI is only compatible with synchronous web frameworks.", IS_TRUE: False},
    {"question": "ASGI is designed specifically for single-threaded web servers.", IS_TRUE: False},
    {"question": "ASGI and WSGI are interchangeable and can be used together seamlessly.", IS_TRUE: False},
    {"question": "ASGI is primarily used for handling synchronous I/O operations in web applications.", IS_TRUE: False},
    {"question": "ASGI applications cannot be deployed on traditional web servers like Apache or Nginx.", IS_TRUE: False},
    {"question": "ASGI is limited to handling only HTTP requests.", IS_TRUE: False},
    {"question": "ASGI is a replacement for the Django framework.", IS_TRUE: False},
    {"question": "ASGI was developed by a consortium of major web server vendors.", IS_TRUE: False},
    {"question": "ASGI is the default interface for building synchronous web applications in Python.", IS_TRUE: False}
]

def get_trivia_questions(QuestionsAmount):
    # URL of the API
    url = f"https://opentdb.com/api.php?amount={QuestionsAmount}&type=boolean"

    # Send a GET request to the API
    response = requests.get(url, timeout=RESPONSE_TIMEOUT)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # If successful, return the response content
        return response.json()
    else:
        # If not successful, print an error message and return None
        print("Failed to retrieve data from the API:", response.status_code)
        return None

def print_question(question_data):
    print("Question:", question_data[QUESTION])
    print("Correct Answer:", question_data[CORRECT_ANSWER])
    print("Incorrect Answers:")
    for answer in question_data['incorrect_answers']:
        print("-", answer)
    print()

def parse_questions(questions):
    parsed_questions = []
    for question in questions:
        if IS_TRUE in question:
            # Predefined question
            correct_answer = str(question[IS_TRUE])
            incorrect_answer = str(not question[IS_TRUE])
        else:
            # API response
            correct_answer = question.get(CORRECT_ANSWER, '').lower()
            incorrect_answer = str(not ('true' in correct_answer))
        
        parsed_question = {
            QUESTION: html.unescape(question.get(QUESTION, '')),
            CORRECT_ANSWER: correct_answer,
            'incorrect_answers': [incorrect_answer]
        }
        parsed_questions.append(parsed_question)
    
    return parsed_questions

def fetch_and_parse_questions(QuestionsAmount):
    try:
        unparsedData = get_trivia_questions(QuestionsAmount)
    except Exception as e:
        logging.WARNING(e)
        unparsedData = None

    if unparsedData is not None:
        # Check if the unparsed data is a dictionary with 'results' key
        if 'results' in unparsedData:
            # Parse the questions from the dictionary structure
            return parse_questions(unparsedData['results'])
        # Check if the unparsed data is a list of dictionaries with 'question' and 'is_true' keys
        elif isinstance(unparsedData, list) and all(isinstance(item, dict) and 'question' in item and 'is_true' in item for item in unparsedData):
            # Parse the questions directly from the list
            return parse_questions(unparsedData)
        else:
            print("Invalid format of unparsed data. Using predefined question bank.")
            return parse_questions(trivia_questions)
    else:
        print("API request failed. Using predefined question bank.")
        return parse_questions(trivia_questions)

class Client(threading.Thread):
    def __init__(self, socket, address, id):
        super().__init__()
        self.socket = socket
        self.address = address
        self.id = id
        self.name = ""
        self.first_message_received = False  # connect msg

    def __str__(self):
        return f"Client {self.id} {self.name} from {str(self.address)}"

class TriviaServer:
    def __init__(self, host, port):
        self.host = host.strip()
        self.port = port
        self.connections = []
        self.total_connections = 0
        self.game_started = False
        self.udp_socket = None

    def accept_clients(self):
        while not self.game_started:
            try:
                client_socket, address = self.server_socket.accept()
                new_client = Client(client_socket, address, self.total_connections)
                new_client.name = new_client.socket.recv(SOCKET_BUFFER_SIZE).decode().strip()
                self.connections.append(new_client)
                print(f"New connection: {new_client.name}")
                self.total_connections += 1
            except socket.timeout:
                break
            except ConnectionResetError:
                print("Connection closed by the client before establishing a connection.")
                continue

    def receive(self, client):
        try:
            while True:
                if not client.first_message_received:
                    # Skip the first message (name of the client, already handled during connection)
                    client.first_message_received = True
                    continue
                
                data = client.socket.recv(SOCKET_BUFFER_SIZE).decode().strip()
                if data:
                    print(f"Client {client.name} answered {data}")
                    # Here, you could add logic to check answers, update scores, etc.
        except ConnectionResetError:
            print(f"Connection closed by client {client.name}")
        except Exception as e:
            print(f"Error receiving data from client {client.name}: {e}")
        finally:
            client.socket.close()
            self.connections.remove(client)


    def manage_trivia_game(self, questions):    
        round_number = 1
        while len(self.connections) > 1 and self.game_started:
            print(f"Round {round_number}, played by: {', '.join(client.name for client in self.connections)}")

            for question in questions:
                question_data = self.format_question(question)
                print(question_data)
                # Using a thread pool to limit the number of threads
                with ThreadPoolExecutor(max_workers=len(self.connections)) as executor:
                    # List to keep track of threads
                    threads = []

                    # Send question to each client concurrently
                    for client in self.connections:
                        thread = threading.Thread(target=self.send_question_to_client, args=(client, question_data))
                        thread.start()
                        threads.append(thread)

                    # Wait for all threads to complete
                    for thread in threads:
                        thread.join()
                        
                responses = {}  # Dictionary to store responses from clients

                self.wait_for_responses(responses)
                if len(responses) == 0:
                    round_number += 1
                    continue
                
                self.process_responses(responses, question)
                if not self.game_started:
                    break

            round_number += 1

        #Game over
        if len(self.connections) <= 1:
            msg = f"Game over!\nCongratulations to the winner: {self.connections[0].name if len(self.connections) == 1 else 'Which isnt here right now'}"            
            self.print_and_broadcast_to_players(msg)
           
            if len(self.connections) == 1:
                self.connections.remove(self.connections[0])
                self.server_socket.close()
                time.sleep(2)                        
            self.game_started = False

    def wait_for_responses(self, responses):
        lock = threading.Lock()
        all_clients_responded = threading.Condition(lock)

        # Start a thread for each player to handle their response
        threads = []
        for client in self.connections:
            t = threading.Thread(target=self.handle_player_response, args=(client, responses, all_clients_responded))
            t.start()
            threads.append(t)

        # Poll until timeout
        timeout = RESPONSE_TIMEOUT  # RESPONSE_TIMEOUT seconds timeout
        start_time = time.time()
        with all_clients_responded:
            while time.time() - start_time < timeout:
                if len(responses) == len(self.connections):
                    break
                all_clients_responded.wait(timeout)

    def handle_player_response(self, client, responses, all_clients_responded):
        try:
            data = client.socket.recv(SOCKET_BUFFER_SIZE).decode("utf-8").strip()
            if data:
                responses[client] = data
                with all_clients_responded:                
                    all_clients_responded.notify_all()
        except Exception as e:
            print(f"Error receiving message from {client.address}: {e}")    

    def process_responses(self, responses, question):
        correct_answer = question[CORRECT_ANSWER]                
        # Convert correct answer to boolean value
        correct_bool_answer = True if correct_answer.lower() == 'true' else False

        correct_players = [client for client, response in responses.items() if RESPONSE_MAP.get(response.strip().upper()) == correct_bool_answer]             
        incorrect_players = [client for client, response in responses.items() if RESPONSE_MAP.get(response.strip().upper()) != correct_bool_answer]

        for client in self.connections:
            if client in correct_players:
                msg = f"Player {client.name} is correct!"
                self.print_and_broadcast_to_players(msg)
            elif client in responses:
                msg = f"Player {client.name} is incorrect!"
                self.print_and_broadcast_to_players(msg)

        # Disqualify players who didn't respond
        for client in self.connections:
            if client not in responses:
                msg = f"Player {client.name} didn't answer in time."
                self.print_and_broadcast_to_players(msg)
                self.disconnectClient(client)

        if len(correct_players) == 1:
            self.game_started = False  # Set game_started to False when a winner is determined

        # Disqualify players who were wrong
        if len(correct_players) > 0:
            for client in incorrect_players:
                self.disconnectClient(client)                         

    def print_and_broadcast_to_players(self, message):
        print(message)
        for client in self.connections:
            try:
                client.socket.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"Error sending message to {client.address}: {e}")                       

    def disconnectClient(self, client):
        self.connections.remove(client)                 

    def format_question(self, question):
        current_question = question[QUESTION]
        possible_answers = ['True', 'False']  # Possible answer choices
        return f"True or False: {current_question}" 

    def send_question_to_client(self, client, question_data):
        try:
            client.socket.sendall(question_data.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message to {client.address}: {e}")

    def start(self):
        while True:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(SOCKET_TIMEOUT)  # Set a timeout for accepting connections
            print(f"Server started, listening on IP address {self.host}")

            self.accept_clients()

            if len(self.connections) > 0:
                self.game_started = True  # Start the game only if there are clients connected
                print("No longer accepting new clients. Game is starting.")

                # Game logic (fetch questions, send them to clients, receive answers, etc.)
                questions = fetch_and_parse_questions(5)

                welcome_message = f"Welcome to the {self.name} server, where we are answering trivia questions about Aston Villa FC.\n"
                welcome_message += "\n".join([f"Player {i+1}: {client.name}" for i, client in enumerate(self.connections)])
                welcome_message += f"\n\nAfter {RESPONSE_TIMEOUT} seconds pass during which no additional player joins, the game begins.\n"
                welcome_message += "The server will now start sending questions. Good luck!\n"
                for client in self.connections:
                    try:
                        print(welcome_message)
                        client.socket.sendall(welcome_message.encode('utf-8'))
                    except Exception as e:
                        print(f"Error sending welcome message to {client.address}: {e}")

                self.manage_trivia_game(questions)

                # Game is over
                self.game_started = False
                print("Game over, sending out offer requests..")
            else:
                print("No clients connected. Waiting for clients to connect.")
      
    def broadcast_offers(self, server_name):
        
        # Ensure the server name is no more than SERVER_NAME_LENGTH characters
        server_name = server_name[:SERVER_NAME_LENGTH]
        # Pad the server name with null characters ('\0') to make it exactly SERVER_NAME_LENGTH characters long
        self.name = server_name.ljust(SERVER_NAME_LENGTH, '\0')
        
        # Pack the message with the server name included
        message = struct.pack(PACK_FORMAT, UDP_HEADER_MAGIC, UDP_HEADER_VERSION, self.name.encode(), self.port)

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, BROADCAST_INTERVAL)

        while True:
            self.udp_socket.sendto(message, ('<broadcast>', self.port))
            time.sleep(1)

def main():
    server = TriviaServer(HOST, PORT)
    threading.Thread(target=server.broadcast_offers, args=("YourServerName",)).start()
    server.start()

    

if __name__ == "__main__":
    main()
