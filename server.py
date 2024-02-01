import socket
import threading
import json
import signal
import sys

import random
import time


host = socket.gethostname() # get the hostname of the machine
print(f"Host: {host}")
hostIP = socket.gethostbyname(host) # convert the hostname to IP 
print(f"Host IP: {hostIP}")
serverPort = 9889
print(f"Server Port: {serverPort}")

class concurrencyLock:
    def __init__(self):
        self.reader = 0 # we allow mutliple readers
        self.lock = threading.Lock() # protect reader counter
        self.readerLock = threading.Lock()
        self.writerLock = threading.Lock()
    
    def acquireRead(self):
        with self.lock:
            self.reader += 1
            if self.reader == 1: # if the first reader, acquire the writer lock
                self.writerLock.acquire()

    def acquireWrite(self):
        self.readerLock.acquire() # wait for all readers to release the lock
        self.writerLock.acquire() # wait for all writers to release the lock

    def releaseRead(self):
        with self.lock:
            self.reader -= 1
            if self.reader == 0:
                self.writerLock.release()

    def releaseWrite(self):
        self.writerLock.release() # other can write
        self.readerLock.release() # other can read

sem = concurrencyLock() # create a semaphore to control the access to the data file

bufferSize = 1024
backlog = 100

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create a new socket for the server
serverSocket.bind((hostIP, serverPort)) # bind the socket to the IP address and port number
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # allow the server to reuse the same port number

def main():
    serverSocket.listen(backlog) # allow 100 connections waiting before refusing new connections
    print(f"The server is listening for incoming connections {hostIP} on port {serverPort}")

    while 1:
        connectionSocket, addr = serverSocket.accept()
        print(f"Connection from {addr} has been established!")
        clientThread = threading.Thread(target=handle_client, args=(connectionSocket, addr))
        clientThread.start()
        clientThread.name = f"Client-{threading.active_count()-1} from {addr[1]}"
        print(f"{clientThread.name} has been started!")

# parser to generate command from memcache client 
def parser(buffer): 
    command, buffer = buffer.split("\r\n", 1) # get the first complete command
    args = command.split()
    return args, buffer

def handle_client(connectionSocket, addr):
    global sem
    # our dear memcache client will send a chunk of data at a time
    buffer = ""
    try:
        while 1:
            data = connectionSocket.recv(bufferSize)
            if not data:
                break  
            buffer += data.decode()

            while "\r\n" in buffer:  # check if there is a complete command in the buffer
                args, buffer = parser(buffer)

                if args[0].lower() == "get":
                    sem.acquireRead()
                    key = args[1]
                    with open("serverStorage.txt", "r") as cache:
                        dataCached = json.load(cache)

                    if key in dataCached:
                        val = dataCached[key]
                        response = f"VALUE {key} 0 {len(val)}\r\n{val}\r\nEND\r\n"
                    else:
                        response = "END\r\n"
                    connectionSocket.send(response.encode())

                    sem.releaseRead()

                elif args[0].lower() == "set":
                    # during the read and write, there is only one thread can access the file
                    sem.acquireWrite()
                    if len(args) < 4: # we are dealing with non-memcache client: set key bytes \r\n 
                        key, bytes = args[1], int(args[2])
                        connectionSocket.send("OK".encode())  # send OK to the client let it continue to send the value
                        value = connectionSocket.recv(bytes).decode()
                        if len(value) != bytes:
                            connectionSocket.send("NOT-STORED\r\n".encode())
                        noreply = False
                        buffer = ""

                    else: # we are dealing with memcache client: set key flags exptime bytes [noreply]\r\n
                        key, _, _, bytes = args[1], args[2], args[3], int(args[4])
                        # our dear memcache client sometimes include noreply argument
                        noreply = (len(args) == 6 and args[5].lower() == "noreply")
                        value = buffer[:bytes]
                        buffer = buffer[bytes+2:]  # +2 for \r\n after the value

                    with open("serverStorage.txt", "r") as cache:
                        dataCached = json.load(cache)

                    dataCached[key] = value
                    with open("serverStorage.txt", "w") as cache:
                        json.dump(dataCached, cache)

                    if not noreply:
                        connectionSocket.send("STORED\r\n".encode())
                    
                    sem.releaseWrite()
                
                elif args[0].lower() == "exit":
                    print(f"Client {addr} is gone!")
                    connectionSocket.close()
                
                else:
                    print("Right now, we only support GET and SET commands.")
                    connectionSocket.send("CONFUSED\r\n".encode())

                    
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        connectionSocket.close()

# during testing I always have to stop the server by ^C
# to make sure the server will close the socket and release the port
def signal_handler(sig, frame):
    print("Exiting the server!")
    serverSocket.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    main()


