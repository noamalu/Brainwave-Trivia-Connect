import concurrent.futures 
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

class TriviaServer(ColoredPrinter):
    def __init__(self, host, port):
        super().__init__()
        self.host = host.strip()
        self.port = port
        self.connections = []
        self.total_connections = 0
        self.game_started = False
        self.udp_socket = None
        self.most_common_character = None
        self.character_counts = {}   
        self.player_stats = {}
        self.start_time = None  # Initialize start_time attribute

    def reset(self):
        # Reset all attributes to their initial state
        self.connections = []
        self.total_connections = 0
        self.game_started = False
        self.player_stats = {}
        self.most_common_character = None
        self.character_counts = {}        

    def accept_clients(self):
        while not self.game_started:
            try:
                client_socket, address = self.server_socket.accept()
                if address not in [client.address for client in self.connections]:
                    new_client = Client(client_socket, address, self.total_connections)
                    new_client.name = new_client.socket.recv(SOCKET_BUFFER_SIZE).decode().strip()
                    self.connections.append(new_client)
                    self.print(f"New connection: {new_client.name}")
                    self.total_connections += 1
            except socket.timeout:
                break
            except ConnectionResetError:
                self.print("Connection closed by the client before establishing a connection.")
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
                    self.print(f"Client {client.name} answered {data}")
                    # Here, you could add logic to check answers, update scores, etc.
        except ConnectionResetError:
            self.print(f"Connection closed by client {client.name}")
        except Exception as e:
            self.print(f"Error receiving data from client {client.name}: {e}")
        finally:
            client.socket.close()
            self.connections.remove(client)


    def manage_trivia_game(self, questions):    
        round_number = 1
        while len(self.connections) > 1 and self.game_started:
            self.print(f"Round {round_number}, played by: {', '.join(client.name for client in self.connections)}")

            for question in questions:
                question_data = self.format_question(question)
                self.print(question_data)
                # Using a thread pool to limit the number of threads
                if len(self.connections) > 1:
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
                if len(self.connections)<=1:
                    self.game_started = False
                    break

            round_number += 1

        #Game over
        if len(self.connections) <= 1:
            msg = f"Game over!\nCongratulations to the winner: {self.connections[0].name if len(self.connections) == 1 else 'Which isnt here right now'}"            
            self.print_and_broadcast_to_players(msg)
            self.print_statistics()

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
        self.start_time = time.time()
        with all_clients_responded:
            while time.time() - self.start_time < timeout:
                if len(responses) == len(self.connections):
                    break
                all_clients_responded.wait(timeout)
        
        # Check for clients who didn't respond and disconnect them
        for client in self.connections:
            if client not in responses:
                self.print(f"Client {client.name} did not respond within the timeout period. Disconnecting...")
                self.disconnectClient(client)
                break  # Disconnect only one client at a time to avoid modifying the list while iterating                

    def handle_player_response(self, client, responses, all_clients_responded):
        try:
            data = client.socket.recv(SOCKET_BUFFER_SIZE).decode("utf-8").strip()
            if data:
                responses[client] = data
                with all_clients_responded:                
                    all_clients_responded.notify_all()
        except Exception as e:
            self.print(f"Error receiving message from {client.address}: {e}")    

    def process_responses(self, responses, question):
        correct_answer = question[CORRECT_ANSWER]                
        # Convert correct answer to boolean value
        correct_bool_answer = True if correct_answer.lower() == 'true' else False        
        
        # Variable to track if any player has answered correctly
        any_player_correct = False

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(responses)) as executor:
            futures = {executor.submit(self.process_response, client, response, correct_bool_answer): client for client, response in responses.items()}
            for future in concurrent.futures.as_completed(futures):
                client = futures[future]
                try:
                    result = future.result()
                    # If any player answered correctly, set the flag to True
                    if result:
                        any_player_correct = True
                except Exception as exc:
                    self.print(f"Error processing response from {client.name}: {exc}")

        # If any player answered correctly, disconnect all clients who were wrong
        if any_player_correct:
            for client, response in responses.items():
                if RESPONSE_MAP.get(response.strip().upper()) != correct_bool_answer:
                    self.disconnectClient(client)

    def process_response(self, client, response, correct_bool_answer):
        try:
            self.update_character_statistics(response)
            if RESPONSE_MAP.get(response.strip().upper()) == correct_bool_answer:
                msg = f"Player {client.name} is correct!"
                self.print_and_broadcast_to_players(msg)
                self.update_player_stats(client.name, True, time.time() - self.start_time)
                # Return True if the player is correct
                return True
            else:
                msg = f"Player {client.name} is incorrect!"
                self.print_and_broadcast_to_players(msg)
                self.update_player_stats(client.name, False, time.time() - self.start_time)
                # Return False if the player is incorrect
                return False
        except Exception as exc:
            raise exc              

    def print_and_broadcast_to_players(self, message):
        self.print(message)
        for client in self.connections:
            try:
                client.socket.sendall(message.encode('utf-8'))
            except Exception as e:
                self.print(f"Error sending message to {client.address}: {e}")                       

    def disconnectClient(self, client):
        self.connections.remove(client)                 

    def update_character_statistics(self, response):
        # Count characters in response
        for char in response:
            if char not in self.character_counts:
                self.character_counts[char] = 0
            self.character_counts[char] += 1

        # Find the most common character
        max_count = 0
        most_common_char = None
        for char, count in self.character_counts.items():
            if count > max_count:
                max_count = count
                most_common_char = char
        
        # Update most common character
        self.most_common_character = most_common_char

    def update_player_stats(self, name, is_correct, response_time):
        if name not in self.player_stats:
            # Initialize stats: [fastest response, total correct, max streak, total connections, current streak]
            self.player_stats[name] = [float('inf'), 0, 0, 0, 0]

        stats = self.player_stats[name]
        stats[0] = min(stats[0], response_time)  # Fastest response
        # Update total correct answers
        if is_correct:
            stats[1] += 1
            # Update current streak
            stats[4] += 1
            # Update max streak
            stats[2] = max(stats[2], stats[4])
        else:
            # Reset current streak if the answer is incorrect
            stats[4] = 0        

    def print_statistics(self):
        self.print("Player Statistics:")
        categories = ['Fastest in the West', 'Chilling Winning', 'Streakingly Good!', 'Lazy Connection AHAHA']

        # Sort player stats outside the loop
        sorted_stats = sorted(self.player_stats.items(), key=lambda x: x[1][0])  # Sort by fastest response time
        if not sorted_stats:
            self.print("No player statistics available.")
            return

        for i, category in enumerate(categories):
            self.print(f"\nTop player for {category}:")
            if category == 'Fastest in the West':
                fastest_player = sorted_stats[0]
                self.print(f"{fastest_player[0]} - {fastest_player[1][0]} seconds")

            elif category == 'Chilling Winning':
                correct_answers = [(player, stats[1]) for player, stats in sorted_stats]
                most_correct_player = max(correct_answers, key=lambda x: x[1])
                self.print(f"{most_correct_player[0]} - {most_correct_player[1]} correct answers")

            elif category == 'Streakingly Good!':
                longest_streak_player = max(sorted_stats, key=lambda x: x[1][2])
                self.print(f"{longest_streak_player[0]} - {longest_streak_player[1][2]} consecutive correct answers")

            elif category == 'Lazy Connection AHAHA':
                slowest_player = sorted_stats[-1]
                self.print(f"{slowest_player[0]} - {slowest_player[1][0]} seconds")

        if self.most_common_character is not None:
            self.print(f"Most Commonly Typed Character: {self.most_common_character}")

    def format_question(self, question):
        current_question = question[QUESTION]
        possible_answers = ['True', 'False']  # Possible answer choices
        return f"True or False: {current_question}" 

    def send_question_to_client(self, client, question_data):
        try:
            client.socket.sendall(question_data.encode('utf-8'))
        except Exception as e:
            self.print(f"Error sending message to {client.address}: {e}")

    def start(self):
        while True:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(SOCKET_TIMEOUT)  # Set a timeout for accepting connections
            self.print(f"Server started, listening on IP address {self.host}")

            self.accept_clients()

            if len(self.connections) > 0:
                self.game_started = True  # Start the game only if there are clients connected
                self.print("No longer accepting new clients. Game is starting.")

                # Game logic (fetch questions, send them to clients, receive answers, etc.)
                questions = fetch_and_parse_questions(5)

                welcome_message = f"Welcome to the {self.name} server, where we are answering trivia questions [sometimes, about ASGI].\n"
                welcome_message += "\n".join([f"Player {i+1}: {client.name}" for i, client in enumerate(self.connections)])
                welcome_message += f"\n\nAfter {RESPONSE_TIMEOUT} seconds pass during which no additional player joins, the game begins.\n"
                welcome_message += "The server will now start sending questions. Good luck!\n"
                for client in self.connections:
                    try:
                        self.print(welcome_message)
                        client.socket.sendall(welcome_message.encode('utf-8'))
                    except Exception as e:
                        self.print(f"Error sending welcome message to {client.address}: {e}")

                self.manage_trivia_game(questions)

                # Game is over
                self.game_started = False
                self.reset()
                self.print("Game over, sending out offer requests..")
            else:
                self.print("No clients connected. Waiting for clients to connect.")
      
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
            time.sleep(0.3)

def get_local_ip_address():
    return socket.gethostbyname(socket.gethostname())

def main():
    server_ip = get_local_ip_address()
    if server_ip is None:
        print("No suitable IP address found.")
        return
    server = TriviaServer(server_ip, PORT)
    threading.Thread(target=server.broadcast_offers, args=("YourServerName",)).start()
    server.start()

    

if __name__ == "__main__":
    main()
