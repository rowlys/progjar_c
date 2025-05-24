from socket import *
import socket
import logging
import time
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import signal
import sys

from file_protocol import  FileProtocol
fp = FileProtocol()


def handle_client(connection, client_address):
    buffer = ""
    logging.warning("Receiving request...")
    try:
        while True:
            data = connection.recv(5 * 1024  * 1024)
            if not data:
                break
            buffer += data.decode()
            if "\r\n\r\n" in buffer:
                break

        if buffer:
            logging.warning("Request fully received.")
            full_request, _ = buffer.split("\r\n\r\n", 1)
            hasil = fp.proses_string(full_request)
            hasil = hasil + "\r\n\r\n"
            connection.sendall(hasil.encode())

    except Exception as e:
        logging.warning(f"Exception while handling client {client_address}: {e}")
    finally:
        connection.close()

class Server:
    def __init__(self, ipaddress = '0.0.0.0', port = 10000, mode = 'thread', pool_size = 1):
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.ip = ipaddress
        self.port = port
        self.mode = mode
        self.pool_size = pool_size
        self.running = True

        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if mode == 'thread':
            self.executor = ThreadPoolExecutor(max_workers=pool_size)
        elif mode == 'process':
            self.executor = ProcessPoolExecutor(max_workers=pool_size)
        else:
            raise ValueError("Mode must be 'thread' or 'process'")

    def start(self):
        logging.warning(f"server berjalan di ip address {self.ip}, {self.port}")
        self.my_socket.bind((self.ip, self.port))
        self.my_socket.listen()
        self.my_socket.settimeout(3.0)

        try:
            while self.running:
                try:
                    conn, addr = self.my_socket.accept()
                    logging.warning(f"connection from {addr}")
                    self.executor.submit(handle_client, conn, addr)
                

                except socket.timeout:
                    continue
                except OSError:
                    break
        finally:
            self.shutdown()


    def shutdown(self):
        logging.warning("Shutting down server...")
        self.running = False
        self.executor.shutdown(wait=True)
        self.my_socket.close()
        logging.warning("Server has shut down.")

    def _signal_handler(self, signum, frame):
        logging.warning(f"Signal {signum} received, shutting down...")
        self.shutdown()
        sys.exit(0)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['thread', 'process'], default='thread')
    parser.add_argument('--port', type=int, default=10000)
    parser.add_argument('--pool', type=int, default=5)

    args = parser.parse_args()

    svr = Server(ipaddress='0.0.0.0', port=args.port, mode=args.mode, pool_size=args.pool)
    try:
        svr.start()
    except KeyboardInterrupt:
        svr.shutdown()

if __name__ == "__main__":
    main()