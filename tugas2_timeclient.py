import socket

def main():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('172.16.16.101', 45000))
                print("connected to server on port 45000.")

                while True:

                        message = input("")
                        s.sendall((message + "\r\n").encode())

                        if message.lower() == 'quit':
                                print("closing client...")
                                break

                        try:
                                s.settimeout(2)  # wait up to 2 seconds
                                response = s.recv(32)
                                if response:
                                        print(response.decode().strip())
                        except socket.timeout:
                                pass  

if __name__ == '__main__':
    main()
