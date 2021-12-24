import random
import requests
import sys
from sockets import client
import os

os.system('clear')

if len(sys.argv) != 2 or (str(sys.argv[1]) != 'login' and str(sys.argv[1]) != 'register'):
    print ("Correct usage: script command")
    print ("Command can be 'register' or 'login'")
    exit()

command = str(sys.argv[1])
url = 'http://localhost:5000/api'

if command == "register":
    print("------Registration------\n")
    username = input("Username: ")
    password = input("Password: ")
    
    data = {"username": username, "password": password}
    r = requests.post(url=f'{url}/register', json=data)

    if r.status_code == 201:
        command = 'login'
    else:
        print(r.json()['message'])
        exit()              # look at this later

if command == 'login':
    print("\n------Login------\n")
    username = input("Username: ")
    password = input("Password: ")
    ip_address = '127.0.0.1'
    port = random.randint(12000, 13000)

    data = {"username": username, "password": password, "ip_address": ip_address, "port": port}
    r = requests.post(url=f'{url}/login', json=data)

    print(r.json()['message'])
    if r.status_code == 200:
        try:
            client.connect(username, ip_address, port)
        except Exception as e:
            print(e)
    else:
        exit()              # look at this later
