from socket import *
import socket
import threading
import logging
import time 
import sys
from datetime import datetime

class ProcessTheClient(threading.Thread):
        def __init__(self,connection,address):
                self.connection = connection
                self.address = address
                threading.Thread.__init__(self)

        def run(self):
                buffer = b""
                while True:
                        data = self.connection.recv(32)
                        if not data:
                                break

                        buffer += data

                        while b'\r\n' in buffer:
                                decoded_request, buffer = buffer.split(b'\r\n', 1)
                                request = decoded_request.decode('utf-8').strip()
                                logging.warning(f"request from {self.connection}: {request}")


                                if request == "TIME":
                                        now = datetime.now().strftime("%H:%M:%S")
                                        now = f"{now}\r\n"
                                        response = f"JAM {now}"
                                        self.connection.sendall(response.encode('utf-8'))

                                elif request == "QUIT":
                                        logging.warning(f"termination request from {self.connection}...")
                                        self.connection.close()
                                        return

                                else:
                                        logging.warning(f"invalid request: {request} from {self.connection}")

                logging.warning(f"terminating connection with {self.connection}")
                self.connection.close()

class Server(threading.Thread):
        def __init__(self):
                self.the_clients = []
                self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                threading.Thread.__init__(self)

        def run(self):
                self.my_socket.bind(('0.0.0.0',45005))
                self.my_socket.listen(1)
                while True:
                        self.connection, self.client_address = self.my_socket.accept()
                        logging.warning(f"connection from {self.client_address}")

                        clt = ProcessTheClient(self.connection, self.client_address)
                        clt.start()
                        self.the_clients.append(clt)


def main():
        svr = Server()
        svr.start()

if __name__=="__main__":
        main()
