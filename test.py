import threading
import socket
import time
import random

def test_client(id, hostIP, serverPort):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # because we test a lot
    clientSocket.connect((hostIP, serverPort))

    clientSocket.send(f"set key 1".encode())
    _ = clientSocket.recv(1024).decode() # we will get OK
    randomValue = random.randint(0, 10)
    clientSocket.send(f"{randomValue}".encode())
    print(f"Client {id} set key with value {randomValue}")
    _ = clientSocket.recv(1024).decode() # we will get STORED
    clientSocket.send("get key".encode())
    response = clientSocket.recv(1024).decode()
    print(f"Client {id} received: {response}")
    clientSocket.send("exit".encode())
    clientSocket.close()


# keep the same host and port number as the server
host = socket.gethostname()
print(f"Host: {host}")
hostIP = socket.gethostbyname(host)  
print(f"Host IP: {hostIP}")
serverPort = 9889
print(f"Server Port: {serverPort}")

numClients = 5

for i in range(numClients):
    thread = threading.Thread(target=test_client, args=(i, hostIP, serverPort))
    thread.start()
