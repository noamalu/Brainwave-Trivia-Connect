from concurrent.futures import ThreadPoolExecutor
import html
import socket
import struct
import threading
import time
from datetime import datetime, timedelta
import requests

trivia_questions = [
    {"question": "Aston Villa has won the English Premier League title more than once.", "is_true": True},
    {"question": "Aston Villa's home ground is Villa Park.", "is_true": True},
    {"question": "Aston Villa was one of the founding members of the English Football League in 1888.", "is_true": True},
    {"question": "Aston Villa has never won the UEFA Champions League.", "is_true": True},
    {"question": "Aston Villa's traditional colors are claret and blue.", "is_true": True},
    {"question": "Aston Villa's nickname is 'The Lions'.", "is_true": True},
    {"question": "Aston Villa holds the record for the most FA Cup final appearances.", "is_true": True},
    {"question": "Aston Villa's all-time leading goal scorer is Billy Walker.", "is_true": False},
    {"question": "Aston Villa has never been relegated from the English Premier League.", "is_true": False},
    {"question": "Aston Villa has won the UEFA Europa League.", "is_true": False},
    {"question": "Aston Villa has never won the Football League Cup.", "is_true": False},
    {"question": "Aston Villa's highest league finish is 2nd place.", "is_true": True},
    {"question": "Aston Villa has a fierce rivalry with Wolverhampton Wanderers.", "is_true": True},
    {"question": "Aston Villa has won the FA Cup more times than any other club.", "is_true": False},
    {"question": "Aston Villa was founded in the 19th century.", "is_true": True},
    {"question": "Aston Villa's record transfer signing is Darren Bent.", "is_true": False},
    {"question": "Aston Villa has won the English top-flight division in the 21st century.", "is_true": False},
    {"question": "Aston Villa's longest-serving manager is Ron Atkinson.", "is_true": False},
    {"question": "Aston Villa has a statue of Cristiano Ronaldo outside Villa Park.", "is_true": False},
    {"question": "Aston Villa has never won the European Cup/Champions League.", "is_true": True}
]

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
# def fetch_and_parse_questions(QuestionsAmount, typeOfAnswers):
#     unparsedData = get_trivia_questions(QuestionsAmount, typeOfAnswers)
#     return parse_questions_response(unparsedData)    

def parse_predefined_questions(questions):
    parsed_questions = []
    for question in questions:
        parsed_question = {
            'question': question['question'],
            'correct_answer': str(question['is_true']),
            'incorrect_answers': [str(not question['is_true'])]
        }
        parsed_questions.append(parsed_question)
    return parsed_questions

def fetch_and_parse_questions(QuestionsAmount, typeOfAnswers):
    try:
        unparsedData = get_trivia_questions(QuestionsAmount, typeOfAnswers)
    except Exception as e:
        print("An error occurred while fetching trivia questions:", e)
        unparsedData = None

    if unparsedData is not None:
        return parse_questions_response(unparsedData)
    else:
        print("API request failed. Using predefined question bank.")
        return parse_predefined_questions(trivia_questions)

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
        self.host = host
        self.port = port
        self.connections = []
        self.total_connections = 0
        self.game_started = False

    def accept_clients(self):
        while not self.game_started:
            try:
                client_socket, address = self.server_socket.accept()
                new_client = Client(client_socket, address, self.total_connections)
                new_client.name = new_client.socket.recv(1024).decode().strip()
                self.connections.append(new_client)
                print(f"New connection: {new_client.name}")
                self.total_connections += 1
            except socket.timeout:
                # If no new connections within a certain time, break the loop
                break
        print("No longer accepting new clients. Game is starting.")

    def receive(self, client):
        try:
            while True:
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

        if len(self.connections) == 1:
            print(f"Game over!\nCongratulations to the winner: {self.connections[0].name}")
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
        timeout = 10  # 10 seconds timeout
        start_time = time.time()
        with all_clients_responded:
            while time.time() - start_time < timeout:
                if len(responses) == len(self.connections):
                    break
                all_clients_responded.wait(timeout=1)

    def handle_player_response(self, client, responses, all_clients_responded):
        try:
            data = client.socket.recv(1024).decode("utf-8").strip()
            if data:
                responses[client] = data
                with all_clients_responded:                
                    all_clients_responded.notify_all()
        except Exception as e:
            print(f"Error receiving message from {client.address}: {e}")    

    def process_responses(self, responses, question):
        correct_answer = question['correct_answer']
        correct_players = [client for client, response in responses.items() if response.strip().lower() == correct_answer.strip().lower()]
        incorrect_players = [client for client, response in responses.items() if response.strip().lower() != correct_answer.strip().lower()]

        for client in self.connections:
            if client in correct_players:
                print(f"Player {client.name} is correct!")
            elif client in responses:
                print(f"Player {client.name} is incorrect!")

        # Disqualify players who didn't respond
        for client in self.connections:
            if client not in responses:
                print(f"Player {client.name} didn't answer in time.")
                self.disqualify(client, "didn't answer in time.")

        if len(correct_players) == 1:
            self.game_started = False  # Set game_started to False when a winner is determined

        # Disqualify players who were wrong
        if len(correct_players) > 0:
            for client in incorrect_players:
                self.disqualify(client, "incorrect answer")                           

    def disqualify(self, client, reason):
        self.connections.remove(client)                 

    def format_question(self, question):
        current_question = question['question']
        possible_answers = [question['correct_answer']] + question['incorrect_answers']
        answers_str = '\n'.join([f"{i+1}) {html.unescape(answer)}" for i, answer in enumerate(possible_answers)])
        return f"True or False: {current_question}"

    def send_question_to_client(self, client, question_data):
        try:
            client.socket.sendall(question_data.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message to {client.address}: {e}")

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(5)  # Set a timeout for accepting connections
        print(f"Server started, listening on IP address {self.host}")

        self.accept_clients()

        self.game_started = True  # Stop accepting new clients and start the game

        # Game logic (fetch questions, send them to clients, receive answers, etc.)
        questions = fetch_and_parse_questions(5, "boolean")
        print_question(questions[0])
        self.manage_trivia_game(questions)

        # Cleanup and closing connections can go here

    def broadcast_offers(self, server_name):
        # Ensure the server name is no more than 32 characters
        server_name = server_name[:32]
        # Pad the server name with null characters ('\0') to make it exactly 32 characters long
        server_name_padded = server_name.ljust(32, '\0')
        
        # Pack the message with the server name included
        message = struct.pack('!Ib32sH', 0xabcddcba, 0x2, server_name_padded.encode(), self.port)

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while True:
            udp_socket.sendto(message, ('<broadcast>', self.port))
            time.sleep(1)

def main():
    server = TriviaServer('10.0.0.9', 13117)
    threading.Thread(target=server.broadcast_offers, args=("YourServerName",)).start()
    server.start()

if __name__ == "__main__":
    main()
