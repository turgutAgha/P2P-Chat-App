import socket
import os
import requests
import pickle
from utils import UDP_MAX_SIZE, encapsulate_message, decapsulate_message

def receive(host: str = '127.0.0.1', port: int = 3000):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    s.bind((host, port))
    print(f'Listening at {host}:{port}')

    members = {}

    while True:
        msg, addr = s.recvfrom(UDP_MAX_SIZE)
        msg_text = decapsulate_message(pickle.loads(msg))
        if not msg:
            continue

        if addr not in members:

            client_id = addr[1]
            if msg_text.startswith('__join'):
                nickname = msg_text.split(":")[1]
                if nickname not in members:
                    message = encapsulate_message("------Welcome to chat!------")
                    s.sendto(pickle.dumps(message), addr)
                    print(f'Client {client_id} [{nickname}] joined chat')
                    members[nickname] = addr
                    continue
                else:
                    message = encapsulate_message("ALERT! This nickname has already been used.")
                    s.sendto(pickle.dumps(message), addr)
        else:
            message = encapsulate_message("ALERT! This address has already been used.")
            s.sendto(pickle.dumps(message), addr)


        if msg_text == '__members':
            message_template = '{}__{}'
            
            print(f'Client {client_id} requested active clients')
            
            active_members = requests.get('http://localhost:5000/api/online_members').json()['members']
            active_members = [f'{m[0]}:{m[1]}' for m in active_members if m[1] != list(addr)]

            members_msg = ';'.join(active_members)
            message = message_template.format('members', members_msg)
            message = encapsulate_message(message)
            
            s.sendto(pickle.dumps(message), addr)

        elif msg_text.startswith('__exit'):
            nickname = msg_text.split(":")[1]
            members.pop(nickname)
            data={"username": nickname}
            requests.post(url=f'http://localhost:5000/api/disconnect', json=data)


if __name__ == '__main__':
    os.system('clear')
    receive()