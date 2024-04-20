# config.py

# Socket settings
SOCKET_BUFFER_SIZE = 1024
SOCKET_TIMEOUT = 10  # Socket timeout for accepting connections

# Timeout settings
RESPONSE_TIMEOUT = 10  # Timeout for waiting for client responses

# Trivia settings
NUM_QUESTIONS_API = 5  # Number of questions to fetch from the API
QUESTION_TYPE = "boolean"  # Type of trivia questions to fetch

# UDP broadcast settings
BROADCAST_INTERVAL = 1  # Interval between UDP broadcast messages (in seconds)
UDP_HEADER_MAGIC = 0xabcddcba  # Magic number for UDP packet header
UDP_HEADER_VERSION = 0x2  # Version number for UDP packet header

# Format string for struct.pack
PACK_FORMAT = '!Ib32sH'

# server name length
SERVER_NAME_LENGTH = 32  # length for the server name

HOST = '10.0.0.9'
PORT = 13117

RESPONSE_MAP = {'Y': True, 'T': True, '1': True, 'N': False, 'F': False, '0': False}

CORRECT_ANSWER = 'correct_answer'
IS_TRUE = 'is_true'
QUESTION = 'question'

