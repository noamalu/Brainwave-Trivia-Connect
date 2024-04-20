# config.py

# Socket settings
SOCKET_BUFFER_SIZE = 1024
SOCKET_TIMEOUT = 10  # Socket timeout for accepting connections 
SAFTY_FIRST = 5
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

#HOST = '10.0.0.9'
PORT = 13117

RESPONSE_MAP = {'Y': True, 'T': True, '1': True, 'N': False, 'F': False, '0': False}

CORRECT_ANSWER = 'correct_answer'
IS_TRUE = 'is_true'
QUESTION = 'question'

BLUE = '\x1b[34m'
WHITE = '\x1b[37m'

class ColoredPrinter:
    def __init__(self):
        self.current_color = BLUE  # Start with blue color

    def print(self, message):
        if self.current_color == BLUE:  # Blue color
            self.current_color = WHITE  # Switch to white color
        else:
            self.current_color = BLUE  # Switch to blue color
        
        print(self.current_color + message)

NAME_BANK = [
    "ByteBandit",
    "DataDynamo",
    "PacketPirate",
    "CyberCircuit",
    "RouterRuler",
    "LANLiberator",
    "ProtocolProwler",
    "FirewallFury",
    "WiFiWizard",
    "NetNinja",
    "SwitchSorcerer",
    "PingPioneer",
    "ModemMaestro",
    "NodeNecromancer",
    "CryptoCrusader",
    "SocketSlinger",
    "FiberFreak",
    "PortPhantom",
    "LANLord",
    "ProtocolProdigy",
    "BandwidthBard",
    "RoutingRogue",
    "PacketProwess",
    "ByteBuccaneer",
    "WirelessWarlock",
    "SwitchSlayer",
    "CyberSavant",
    "DataDaredevil",
    "FirewallFencer",
    "LANLuminary",
    "PingPirate",
    "ModemMaster",
    "NodeNavigator",
    "CryptoConqueror",
    "SocketSavvy"
]
