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
    
    return parsed_questions

def fetch_and_parse_questions(QuestionsAmount, typeOfAnswers):
    unparsedData = get_trivia_questions(QuestionsAmount, typeOfAnswers)
    return parse_questions_response(unparsedData)    

#Variables for holding information about connections
connections = []
total_connections = 0

#Client class, new instance created for each connected client
#Each instance has the socket and address that is associated with items
#Along with an assigned ID and a name chosen by the client
class Client(threading.Thread):
    def __init__(self, socket, address, id, name, signal):
        threading.Thread.__init__(self)
        self.socket = socket
        self.address = address
        self.id = id
        self.name = name
        self.signal = signal
    
    def __str__(self):
        return str(self.id) + " " + str(self.address)
    
    #Attempt to get data from client
    #If unable to, assume client has disconnected and remove him from server data
    #If able to and we get data back, print it in the server and send it back to every
    #client aside from the client that has sent it
    #.decode is used to convert the byte data into a printable string
    def run(self):
        self.name = self.socket.recv(1024).decode().strip() # get client's name
        print(f"Client {self.id} Name: {self.name}")
        while self.signal:
            try:
                data = self.socket.recv(32)
                    ###################################################################
                # TODO: this part supposed to check the client's answer to the trivia question,
                #       might go into "game room class instead"
                    ###################################################################
                if data: 
                    print(f"todo: check if this answer received from {self.name} is true/false")
                    for client in connections:
                        client.socket.sendall(data)
            except:
                print(f"Client {self.id} {self.name} has disconnected")
                self.signal = False
                connections.remove(self)
                break
            if data != "":
                print("ID " + str(self.id) + ": " + str(data.decode("utf-8")))
                for client in connections:
                    if client.id != self.id:
                        client.socket.sendall(data)

#Wait for new connections
def newConnections(socket):
    last_connection_time = datetime.now()
    while True:
        sock, address = socket.accept()
        global total_connections
        connections.append(Client(sock, address, total_connections, "Name", True))
        connections[len(connections) - 1].start()
        print("New connection at ID " + str(connections[len(connections) - 1]))
        total_connections += 1
        print(f"total connections ={total_connections}")
        if datetime.now() - last_connection_time > timedelta(seconds=7):
            print("the cycle is over - the avatar is dead")
            break


def broadcastOffers():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message = struct.pack('!IbH', 0xabcddcba, 0x2, 13117)  # Magic cookie, message type, server port
    
    i=0
    while True: 
        udp_socket.sendto(message, ('<broadcast>', 13117))
        time.sleep(1)
        

# def send_message_to_all_clients(message):
    
#     for client in connections:  # Assume 'connections' is your list of client threads
#         try:
#             print("i have entered\n")
#             client.socket.sendall(message.encode('utf-8'))
#         except Exception as e:
#             print(f"Error sending message to {client.address}: {e}")

def send_message_to_all_clients(message):
    decoded_message = html.unescape(message)
    for client in connections:  # Assume 'connections' is your list of client threads
        try:
            client.socket.sendall(decoded_message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message to {client.address}: {e}")


def main():
    #Get host and port
    host = '0.0.0.0'  # Listen on all interfaces (possible also - "localhost")
    port = 13117

    #Create new server socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen()
    print(f"Server started, listening on IP address {host}")

    # Start broadcasting offers
    threading.Thread(target=broadcastOffers, args=()).start()

    # Start accepting connections
    newConnections(sock)
    print("yalla   aaaaa")


    # Prevent the main thread from exiting
    try:
        questions = fetch_and_parse_questions(10, "boolean") #another option is multiple   
        # send_message_to_all_clients("Hello, clients! This is your captain speaking, we are heading towards the iceberg!")     
        send_message_to_all_clients("Let's start playing!\n")
        print(questions[0]['question'])
        send_message_to_all_clients(questions[0]['question'])

        # while True:
        #     # print("I am sending a msg to all my children\n")
        #     time.sleep(2)
    except KeyboardInterrupt:
        print("Server is shutting down.")
        # Add any cleanup code here (closing sockets, etc.)
    
    

if __name__ == "__main__":
    main()