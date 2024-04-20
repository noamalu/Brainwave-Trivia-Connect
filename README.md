<span style="color:#383838"># Trivia Game Server</span>

This project is a multiplayer trivia game server where clients can connect and participate in answering trivia questions. The server supports both human clients and bot clients. Clients connect to the server using TCP sockets.

## Files

### `server-app.py`

This file contains the main server application. It handles accepting connections from clients, managing the trivia game rounds, sending questions to clients, receiving answers, and determining winners. It also includes functionality to broadcast server offers using UDP.

### `clientApp.py`

This file contains the code for the human client. It connects to the server, receives trivia questions, prompts the user for answers, and sends the answers back to the server.

### `bot-app.py`

This file contains the code for the bot client. It simulates a client connecting to the server, receiving trivia questions, and sending random answers back to the server.

### `config.py`

This file contains configuration settings for the server and clients, such as socket buffer size, timeouts, trivia settings, and server name length. It also includes a dictionary mapping shorthand responses to boolean values.

## Usage

1. Start the server by running `server-app.py`.
2. Clients (human or bot) can then connect to the server using `clientApp.py` or `bot-app.py`.
3. Once clients are connected, the server starts sending trivia questions.
4. Clients respond with their answers, and the server determines the winners based on correctness and response time.
5. The game continues until there's a single winner or all clients are disconnected.

## Dependencies

- Python 3.x
- `requests` library (for fetching trivia questions from an API)

## Running the Server

To start the server, run `server-app.py`:

```
python server-app.py
```

The server will start listening for incoming connections.

## Connecting Clients

To connect a human client, run `clientApp.py`:

```
python clientApp.py
```

To connect a bot client, run `bot-app.py`:

```
python bot-app.py
```

## Configuration

You can adjust configuration settings such as socket buffer size, timeouts, and trivia settings in `config.py`.
