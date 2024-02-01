from pymemcache.client import base
import socket

# keep the same host and port number as the server
host = socket.gethostname()
print(f"Host: {host}")
hostIP = socket.gethostbyname(host)  
print(f"Host IP: {hostIP}")
serverPort = 9889
print(f"Server Port: {serverPort}")

def test():
    client = base.Client((hostIP, serverPort))
    client.set('some_key', 'some_value')
    result = client.get('some_key')
    print(f"Get result: {result}")
    client.close()

if __name__ == "__main__":
    test()
