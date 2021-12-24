UDP_MAX_SIZE = 65535

COMMANDS = (
    '/members',
    '/connect',
    '/exit',
    '/help',
)

HELP_TEXT = """
/members - get active members
/connect <client> - connect to member
/exit - disconnect from client
/help - show this message
"""

CHECKSUM = 6

def create_checksum(msg):
    s = 0

    # add null byte for making message length even number
    if len(msg) % 2:
        msg += "\0"

    # loop taking 2 characters at a time
    for i in range(0, len(msg), 2):
        w = (ord(msg[i]) << 8) + ord(msg[i+1])
        s += w

    s = (s>>16) + (s & 0xffff)

    #complement and mask to 4 byte short
    s = ~s & 0xffff

    return s


def verify_checksum(msg, checksum):
    if (len(msg) % 2) == 1:
        msg += "\0"
    
    for i in range(0, len(msg), 2):
        w = (ord(msg[i]) << 8) + ord(msg[i + 1])
        checksum += w
        checksum = (checksum >> 16) + (checksum & 0xFFFF)

    return checksum


def encapsulate_message(message):
    checksm = str(create_checksum(message))
    packet = f"{checksm:6}{message}"
    return packet


def decapsulate_message(packet):
    checksm, message = int(packet[:CHECKSUM].strip()), packet[CHECKSUM:]
    verify = verify_checksum(message, checksm)
    if verify == 0xFFFF:
        return message
    else:
        return ("Checksum error!")
