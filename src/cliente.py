#!/usr/bin/env python3
import socket
import ssl

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 4000  # The port used by the server


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sockt:
        sockt.connect((HOST, PORT))
        while True:
            v = input("JogoDaVelha> ")
            comando = v.split()
            if comando[0] == "login":
                # Manda uma mensagem indicando ao servidor a necessidade de iniciar um 'handshake' SSL
                sockt.sendall(bytes('login', 'ascii'))
                # Realiza o wrap no socket e retorna um socket SSL
                wrappedSocket = ssl.wrap_socket(sockt, keyfile="cert/MyKey.key", certfile="cert/MyCertificate.crt")
                # Envia as credenciais de forma segura
                wrappedSocket.send(bytes(comando[1] + ' ' + comando[2], 'ascii'))
                # Realiza o unwrap e retorna um socket comum
                sockt = wrappedSocket.unwrap()
                continue
            if v == "exit":
                break
            sockt.sendall(bytes(v, 'ascii'))
            data = sockt.recv(1024)
            print('Received', repr(data))


if __name__ == '__main__':
    main()
