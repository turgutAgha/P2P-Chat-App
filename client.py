import socket
import threading
import sys
import pickle
from utils import UDP_MAX_SIZE, COMMANDS, HELP_TEXT, encapsulate_message, decapsulate_message


members = {}

def receive(s: socket.socket, host: str, port: int):
    while True:
        msg, addr = s.recvfrom(UDP_MAX_SIZE)
        allowed_addrs = threading.current_thread().allowed_addrs
        if addr not in allowed_addrs:
            continue
        
        
        msg = decapsulate_message(pickle.loads(msg))
        # print(msg)
        if not msg:
            continue

        # packet = decapsulate_message(msg)

        # if packet == "Checksum error!":
        #     print(packet)
        #     continue

        # msg = packet['msg']

        if '__' in msg:
            command, content = msg.split('__')
            if command == 'members':
                members.clear()
                if len(content) == 0:
                    print('\r\r' + 'There is no active member.\nyou: ', end='')
                    continue
                for n, member in enumerate(content.split(';'), start=1):
                    nick, paddr = member.split(":")
                    paddr = tuple(eval(paddr))
                    # print(nick, paddr)
                    members[nick] = paddr    
                    print('\r\r' + f'{n}) {nick}' + '\n' + 'you: ', end='')
        else:
            peer_name = allowed_addrs[addr]
            if addr == (host, port):
                if msg.startswith('ALERT'):
                    print('\r\r' + f'{peer_name}: '+ msg + '\n', end='')
                    s.close()
                    sys.exit(0)
                else:
                    print('\r\r' + msg + '\nyou: ', end='')

            else:
                print('\r\r' + f'{peer_name}: '+ msg + '\nyou: ', end='')


def start_listen(target, socket, host, port):
    th = threading.Thread(target=target, args=(socket, host, port), daemon=True)
    th.start()
    return th


def connect(nickname, ip_address, own_port,  host: str = '127.0.0.1', port: int = 3000):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # own_port = random.randint(12000, 13000)
    s.bind((ip_address, own_port))
    sendto = (host, port)

    listen_thread = start_listen(receive, s, host, port)
    allowed_addrs = {}
    allowed_addrs[sendto] = 'Server'
    listen_thread.allowed_addrs = allowed_addrs
    message = encapsulate_message(f'__join:{nickname}')
    s.sendto(pickle.dumps(message), sendto)
    nick = 'Server'
    while True:
        msg = input(f'\r\ryou: ')

        command = msg.split(' ')[0]
        if command in COMMANDS:
            if msg == '/members':
                message = encapsulate_message('__members')
                s.sendto(pickle.dumps(message), (host, port))

            elif msg == '/exit':
                # peer_port = sendto[-1]
                print(f'Disconnected from {allowed_addrs[sendto]}')
                allowed_addrs.pop(sendto)
                if sendto == (host, port):
                    print("Exited from chat.")
                    message = encapsulate_message(f'__exit:{nickname}')
                    s.sendto(pickle.dumps(message), sendto)
                    s.close()
                    sys.exit(0)
                sendto = (host, port)

            elif msg.startswith('/connect'):
                nick = msg.split(' ')[-1]
                # print(members, members[nick])
                try:
                    # peer_port = int(peer.replace('client', ''))
                    paddr = members[nick]
                    allowed_addrs[paddr] = nick
                    sendto = paddr
                    print(f'Connect to client {nick}')
                except:
                    print(f"Client {nick} is not in members.")

            elif msg == '/help':
                print(HELP_TEXT)
        else:
            msg = encapsulate_message(msg)
            for adds_ in allowed_addrs:
                if adds_ != (host, port):
                    s.sendto(pickle.dumps(msg), adds_)
