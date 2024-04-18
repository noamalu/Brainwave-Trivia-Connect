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
            print(f"Received offer from server {new_client.name} at address {address[0]}, attempting to connect...")
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
        
def send_question_to_client(client, question_data):
    try:
        client.socket.sendall(question_data.encode('utf-8'))
    except Exception as e:
        print(f"Error sending message to {client.address}: {e}")

def manage_trivia_game(questions, connections):    
    global game_started
    round_number = 1
    while len(connections) > 1:
        print(f"Round {round_number}, played by: {', '.join(client.name for client in connections)}")

        for question in questions:
            question_data = format_question(question)
            
            # Using a thread pool to limit the number of threads
            with ThreadPoolExecutor(max_workers=len(connections)) as executor:
                # Send question to each client concurrently
                for client in connections:
                    executor.submit(send_question_to_client, client, question_data)

            responses = {}  # Dictionary to store responses from clients

            wait_for_responses(responses, connections)
            if len(responses) == 0:
                round_number+=1
                break
            
            process_round = process_responses(responses, connections, question)
            if  process_round == -1: 
                game_started = False
                return
            elif process_round == 2:
                round_number+=1
                break

            # Check if all players have been disqualified
            if not connections:
                print("All players disqualified. Game over.")
                game_started = False
                return  # Exit the loop and end the game

        round_number += 1

    if len(connections) == 1:
        print(f"Game over!\nCongratulations to the winner: {connections[0].name}")
        game_started = False


def handle_player_response(client, responses, all_clients_responded):
    try:
        data = client.socket.recv(1024).decode("utf-8").strip()
        if data:
            responses[client] = data
            with all_clients_responded:
                all_clients_responded.notify_all()
    except Exception as e:
        print(f"Error receiving message from {client.address}: {e}")

def format_question(question):
        current_question = question['question']
        possible_answers = [question['correct_answer']] + question['incorrect_answers']
        answers_str = '\n'.join([f"{i+1}) {html.unescape(answer)}" for i, answer in enumerate(possible_answers)])
        return f"Question: {current_question}\n{answers_str}"

def wait_for_responses(responses, connections):
    lock = threading.Lock()
    all_clients_responded = threading.Condition(lock)

    # Start a thread for each player to handle their response
    threads = []
    for client in connections:
        t = threading.Thread(target=handle_player_response, args=(client, responses, all_clients_responded))
        t.start()
        threads.append(t)

    # Poll until timeout
    timeout = 10  # 10 seconds timeout
    start_time = time.time()
    with all_clients_responded:
        while time.time() - start_time < timeout:
            if len(responses) == len(connections):
                break
            all_clients_responded.wait(timeout=1)

def process_responses(responses, connections, question):
    correct_answer = question['correct_answer']
    correct_players = [client for client, response in responses.items() if response.strip().lower() == correct_answer.strip().lower()]
    incorrect_players = [client for client, response in responses.items() if response.strip().lower() != correct_answer.strip().lower()]

    for client in connections:
        if client in correct_players:
            print(f"Player {client.name} is correct!")
        elif client in responses:
            print(f"Player {client.name} is incorrect!")

    # Disqualify players who didn't respond
    for client in connections:
        if client not in responses:
            disqualify(client, "didn't answer in time.")

    if len(correct_players) == 1:
        print(f"{correct_players[0].name} Wins!\nGame over!\nCongratulations to the winner: {correct_players[0].name}")
        return -1 # Exit the loop and end the game

    # Disqualify players who were wrong
    if len(correct_players) > 0:
        for client in incorrect_players:
            disqualify(client, "incorrect answer")
    else:
        return 2


def disqualify(client, reason):
    print(f"Player {client.name} {reason}. Disqualifying...")
    # Send disqualification message to the client
    send_question_to_client(client, f"{reason}. You are disqualified.")
    connections.remove(client)        

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
    manage_trivia_game(questions, connections)
    for client in connections:
        threading.Thread(target=receive, args=(client,)).start()

    # Cleanup and closing connections can go here

if __name__ == "__main__":
    main()