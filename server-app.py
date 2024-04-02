import socket
import threading
import time
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
            'question': result.get('question', ''),
            'correct_answer': result.get('correct_answer', ''),
            'incorrect_answers': result.get('incorrect_answers', [])
        }
        parsed_questions.append(parsed_question)
    
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
        while self.signal:
            try:
                data = self.socket.recv(32)
            except:
                print("Client " + str(self.address) + " has disconnected")
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
    while True:
        sock, address = socket.accept()
        global total_connections
        connections.append(Client(sock, address, total_connections, "Name", True))
        connections[len(connections) - 1].start()
        print("New connection at ID " + str(connections[len(connections) - 1]))
        total_connections += 1

def main():
    questions = fetch_and_parse_questions(10, "boolean") #another option is boolean

    #Get host and port
    host = 'localhost'
    port = 13117

    #Create new server socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(5)

    #Create new thread to wait for connections
    newConnectionsThread = threading.Thread(target = newConnections, args = (sock,))
    newConnectionsThread.start()
    # Prevent the main thread from exiting
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server is shutting down.")
        # Add any cleanup code here (closing sockets, etc.)


main()