from socket import *
import socket
import threading
import logging
import time
import sys


from file_protocol import  FileProtocol
fp = FileProtocol()


class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        self.running = True
        threading.Thread.__init__(self)

    def run(self):
        buffer = ""
        while self.running:
            data = self.connection.recv(32)
            buffer += data.decode()            


            if "\r\n\r\n" in buffer:
                full_request, _ = buffer.split("\r\n\r\n", 1)
                hasil = fp.proses_string(full_request)
                hasil=hasil+"\r\n\r\n"
                self.connection.sendall(hasil.encode())
                break
        self.connection.close()


class Server(threading.Thread):
    def __init__(self,ipaddress='0.0.0.0',port=8881):
        self.ipinfo=(ipaddress,port)
        self.running = True
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(1)
        self.my_socket.settimeout(3.0)

        while self.running:
            try:
                self.connection, self.client_address = self.my_socket.accept()
                logging.warning(f"connection from {self.client_address}")

                clt = ProcessTheClient(self.connection, self.client_address)
                clt.start()
                self.the_clients.append(clt)

            except socket.timeout:
                continue
            except OSError:
                break

        logging.warning("Server shutting down...")
        for client in self.the_clients:
                client.running = False
                client.join()

        self.my_socket.close()
        logging.warning("Server has shut down.")

    def stop(self):
        logging.warning("Stopping server...")
        self.running = False
        self.my_socket.close()


def main():
    svr = Server(ipaddress='0.0.0.0',port=10000)
    svr.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        svr.stop()
        svr.join()


if __name__ == "__main__":
    main()