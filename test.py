import threading
import socket
import time
import random
from pymemcache.client.base import Client

lock = threading.Lock() # make sure print happend immediately after set/get

def delay():
    # generate a random delay time 
    delayTime = random.randint(0, 1)
    time.sleep(delayTime)


def test_client(id, hostIP, serverPort, set_key=True):
    client = Client((hostIP, serverPort))
    delay()
    if set_key:
        lock.acquire()
        randomValue = random.randint(0, 10)
        client.set("key", str(randomValue))
        print(f"Client {id} set key with value {randomValue}")
        lock.release()
    else:
        lock.acquire()
        response = client.get("key").decode()
        print(f"Client {id} received: {response}")
        lock.release()

    client.close()


# keep the same host and port number as the server
host = socket.gethostname()
print(f"Host: {host}")
hostIP = socket.gethostbyname(host)  
print(f"Host IP: {hostIP}")
serverPort = 9889
print(f"Server Port: {serverPort}")

numClients = 50

if __name__ == "__main__":
    for i in range(numClients):
        thread = threading.Thread(target=test_client, args=(i, hostIP, serverPort, i%3==0))
        thread.start()
