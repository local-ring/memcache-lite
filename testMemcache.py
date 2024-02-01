from pymemcache.client.base import Client
import socket

# keep the same host and port number as the server
host = socket.gethostname()
print(f"Host: {host}")
hostIP = socket.gethostbyname(host)  
print(f"Host IP: {hostIP}")
serverPort = 9889
print(f"Server Port: {serverPort}")

def test():
    client = Client((hostIP, serverPort))
    client.set('some_key', 'no_value') # just like me
    client.set('high_key', '2')
    result = client.get('some_key').decode()
    print(f"Get result: {result if result else 'None'}")
    print(client.get('high_key').decode())
    client.close()

if __name__ == "__main__":
    test()
