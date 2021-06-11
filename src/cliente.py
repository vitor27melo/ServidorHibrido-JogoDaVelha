#!/usr/bin/env python3
from threading import Thread
import socket
import ssl

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 4000  # The port used by the server

def recv_packets(sockt):
    while True:
        try:
            data = sockt.recv(1024).decode("utf-8")
        except:
            break
        if (data == 'heartbeat'):
            pass
        else:
            print('Received', data)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sockt:
        sockt.connect((HOST, PORT))

        thread_heartbeat =  Thread(target = recv_packets, args=(sockt,))
        thread_heartbeat.start()

        while True:
            v = input("JogoDaVelha> ")
            comando = v.split()
            if comando:
                if comando[0] == "login":
                    # Manda uma mensagem indicando ao servidor a necessidade de iniciar um 'handshake' SSL
                    sockt.sendall(bytes('login', 'ascii'))
                    # Realiza o wrap no socket e retorna um socket SSL
                    # print("VERSÃO",ssl.SSLContext(ssl.PROTOCOL_TLS))
                    # wrappedSocket = ssl.wrap_socket(sockt, keyfile="cert/MyKey.key", certfile="cert/MyCertificate.crt", 
                    #                                 ssl_version=ssl.PROTOCOL_TLS_CLIENT, cert_reqs=ssl.CERT_NONE)
                    wrappedSocket = ssl.wrap_socket(sockt, ssl_version=ssl.PROTOCOL_TLS)
                    # Envia as credenciais de forma segura
                    wrappedSocket.send(bytes(comando[1] + ' ' + comando[2], 'ascii'))
                    # Realiza o unwrap e retorna um socket comum
                    sockt = wrappedSocket.unwrap()
                    continue
                sockt.sendall(bytes(v, 'ascii'))
                if v == "exit":
                    sockt.close()
                    break
            


if __name__ == '__main__':
    main()
