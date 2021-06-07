#!/usr/bin/env python3
import socket
import ssl


HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 4000        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while (True):
        v = input("Mensagem: ")
        comando = v.split()
        if (comando[0] == "login"):
            s.sendall(bytes('login', 'ascii'))
            # s.recv(1024)
            wrappedSocket = ssl.wrap_socket(s, keyfile="cert/MyKey.key", certfile="cert/MyCertificate.crt")
            wrappedSocket.send(bytes('login 6542315 648564', 'ascii'))
            input("fds")

        if (v == "exit"):
            break
        s.sendall(bytes(v, 'ascii'))
        # data = s.recv(1024)
        # print('Received', repr(data))

