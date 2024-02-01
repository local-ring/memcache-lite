import socket
import signal
import sys

# keep the same host and port number as the server
host = socket.gethostname()
print(f"Host: {host}")
hostIP = socket.gethostbyname(host)  
print(f"Host IP: {hostIP}")
serverPort = 9889
print(f"Server Port: {serverPort}")

bufferSize = 1024
# backlog = 100
serverPort = 9889

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
clientSocket.connect((hostIP, serverPort))

# in case user interrupt the client by ^C
def signal_handler(sig, frame):
    print("Exiting the client!")
    clientSocket.send("exit".encode())
    clientSocket.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    while 1:
        command = input("Enter a command: ") 
        if not command: # in case the user press return because of excitement
            continue
        command += "\r\n"

        clientSocket.send(command.encode()) # first tell the server what command to execute even exit
        if command == "exit":
            print("Exiting the client!")
            break
        response = clientSocket.recv(bufferSize).decode()
        if response == "OK": # continue to send the value we want to SET
            command = input("Enter the value of key: ")
            clientSocket.send(command.encode())
            response = clientSocket.recv(bufferSize).decode()
            print(response)
        elif response == "CONFUSED":
            continue
        else: # the response from server is the value of the key we want to GET
            print(response)


if __name__ == "__main__":
    main()
