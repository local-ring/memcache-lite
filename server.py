import socket
import threading
# import os
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

fileLock = threading.Lock() # ensure that only one thread can access the data file at a time

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

def delay():
    # generate a random delay time 
    delayTime = random.randint(0, 1)
    time.sleep(delayTime)

# make it memchae compatible
def parseCommand(command, connectionSocket):
    key, flags, exptime, bytes, noreply = command[1], command[2], command[3], command[4], command[5]
    print(f"key: {key}, flags: {flags}, exptime: {exptime}, bytes: {bytes}, noreply: {noreply}")
    connectionSocket.recv()
    data_block = connectionSocket.recv(int(bytes)).decode()
    return key, bytes, noreply, data_block

def handle_client(connectionSocket, addr):
    while 1:
        read_line = connectionSocket.recv(bufferSize).decode()
        if not read_line:
            break
        print(f"Received command: {read_line}")

        # parse the command
        longCommand = read_line.strip().split()
        print(f"Long command: {longCommand}")
        command = longCommand[0].lower()

        if not command:
            break

        if command[0] == "get": # the command is get <key> \r\n
            key = command[1]

            delay() # delay before actually reading

            with fileLock:
                with open("serverStorage.txt", "r") as cache:
                    for line in cache:
                        dataCached =  json.loads(line)

            if key in dataCached:
                val = dataCached[key]
                """
                we should respond with two lines
                VALUE <key> <bytes> \r\n
                <data block>\r\n 
                END\r\n
                """
                response = "VALUE " + key + " " + str(len(val)) + "\r\n" + val + "\r\n" + "END\r\n"
            else:
                response = "No such key exists in the cache. \r\n END"
            
            connectionSocket.send(response.encode())  # send the response to the client
            
        elif command[0] == "set": # the command is  set <key> <value-size-bytes> \r\n <value> \r\n 
            key, size = command[1], command[2]
            if len(longCommand) == 5:
                key, size, noreply, val = parseCommand(longCommand, connectionSocket)
            else:
                connectionSocket.send("OK".encode())  # send OK to the client let it continue to send the value
                val = connectionSocket.recv(int(size)).decode()
            if len(val) != int(size) and noreply != "noreply":
                response = "NOT-STORED\r\n"
                connectionSocket.send(response.encode())  # send the response to the client
                continue

            delay() # delay before actually writing
            
            prevData = {}
            # during the read and write, there is only one thread can access the file
            with fileLock:                 
                with open("serverStorage.txt", "r") as cache:
                    for line in cache:
                        prevData = json.loads(line)

                # update the data or add the new pair
                prevData[key] = val
                with open("serverStorage.txt", "w") as cache:
                    cache.write(json.dumps(prevData) + "\n")
            response = "STORED\r\n"
            if noreply != "noreply":
                connectionSocket.send(response.encode())  # send the response to the client
        
        elif command[0] == "exit":  # TODO: figure out how to handle ^C
            print("The client is gone!")
            break
            
        else:
            print("Not supported command: " + command[0])
            print("Right now, we only support GET and SET command.")
            connectionSocket.send("CONFUSED".encode())


# during testing I always have to stop the server by ^C
# to make sure the server will close the socket and release the port
def signal_handler(sig, frame):
    print("Exiting the server!")
    serverSocket.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    main()


