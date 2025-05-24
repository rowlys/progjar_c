import socket
import json
import base64
import logging
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import argparse
import time

logging.basicConfig(level=logging.WARNING)

def send_command(command_str, server_address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    #logging.warning(f"Connecting to {server_address}")
    try:
        #logging.warning("Sending message")
        sock.sendall(command_str.encode())

        data_received = ""
        while True:
            data = sock.recv(5 * 1024 * 1024)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break

        hasil = json.loads(data_received)
        #logging.warning("Data received from server")
        return hasil
    except Exception as e:
        #logging.warning(f"Error during data receiving: {e}")
        return False
    finally:
        sock.close()

def remote_list(server_address):
    command_str = "LIST\r\n\r\n"
    hasil = send_command(command_str, server_address)
    if hasil and hasil['status'] == 'OK':
        print("Daftar file:")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal mengambil daftar file")
        return False

def remote_get(server_address, filename=""):
    command_str = f"GET {filename}\r\n\r\n"
    hasil = send_command(command_str, server_address)
    if hasil and hasil['status'] == 'OK':
        namafile = hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        with open(namafile, 'wb') as fp:
            fp.write(isifile)
        return True
    else:
        #print("Gagal mengunduh file")
        return False

def remote_upload(server_address, filename=""):
    if not os.path.exists(filename):
        print("File not found:", filename)
        return False

    with open(filename, 'rb') as f:
        content = f.read()
        encoded = base64.b64encode(content).decode()

    command_str = f"UPLOAD {filename} {encoded}\r\n\r\n"
    hasil = send_command(command_str, server_address)
    if hasil and hasil['status'] == 'OK':
        #print("Upload sukses")
        return True
    else:
        #print("Gagal mengunggah file")
        return False

def remote_delete(server_address, filename=""):
    command_str = f"DELETE {filename}\r\n\r\n"
    hasil = send_command(command_str, server_address)
    if hasil and hasil['status'] == 'OK':
        print("File berhasil dihapus")
        return True
    else:
        print("Gagal menghapus file")
        return False

def perform_operation(op, filename, server_address):
    if op == "upload":
        return remote_upload(server_address, filename)
    elif op == "download":
        return remote_get(server_address, filename)
    elif op == "delete":
        return remote_delete(server_address, filename)
    elif op == "list":
        return remote_list(server_address)
    else:
        raise ValueError("Unknown task")

def run_concurrent(op, file, filesize, server_address, mode="thread", workers=1):
    success = 0
    executor_cls = ThreadPoolExecutor if mode == "thread" else ProcessPoolExecutor

    with executor_cls(max_workers=workers) as executor:
        futures = [
            executor.submit(perform_operation, op, file, server_address)
            for _ in range(workers)
        ]
        results = [f.result() for f in as_completed(futures)]

        for r in results:
            if r:
                success += 1
        
    return success

if __name__ == '__main__':
    os.makedirs('files_client', exist_ok=True)
    os.chdir('files_client/')

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="172.16.16.101")
    parser.add_argument("--port", type=int, default=10000)
    parser.add_argument("--op", choices=["upload", "download", "delete", "list"], required=True)
    parser.add_argument("--file", default="pokijan.jpg")
    parser.add_argument("--filesize", type=int, default=10)
    parser.add_argument("--mode", choices=["thread", "process"], default="thread")
    parser.add_argument("--workers", type=int, default=1)

    args = parser.parse_args()
    server_address = (args.ip, args.port)

    start_time = time.time()
    success = run_concurrent(args.op, args.file, args.filesize, server_address, args.mode, args.workers)

    

    end_time = time.time()
    total_time = end_time - start_time
    throughput = (args.filesize * 1024 * 1024 * success) / total_time


    print(f"{args.mode} {args.op} {args.filesize} {args.workers} {total_time:.2f} {throughput:.2f} {success} {args.workers - success}")
