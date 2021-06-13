#!/usr/bin/env python3
from threading import Thread
import socket
import ssl
import os
from time import sleep


HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 4000  # The port used by the server
PORT_SSL = 4001  # The port used by the server

class Cliente():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_ssl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORT))
        self.socket_ssl.connect((HOST, PORT_SSL))
        self.socket_ssl = ssl.wrap_socket(self.socket_ssl, ssl_version=ssl.PROTOCOL_TLS)
        self.usuario = None
        self.msg_usuario = ''
        self.busy_printing = False

    def run(self):
        with self.socket:
            thread_recv =  Thread(target = self.recv_packets, args=(self.socket,))
            thread_recv.start()

            thread_recv_encrypted =  Thread(target = self.recv_packets, args=(self.socket_ssl,))
            thread_recv_encrypted.start()

            # self.imprime()
            while True:
                entrada = input("JogoDaVelha> ")
                self.msg_usuario = ' '
                comando = entrada.split()
                if entrada == "exit":
                    self.socket_ssl.sendall(bytes(entrada, 'ascii'))
                    self.socket.sendall(bytes(entrada, 'ascii'))
                    self.socket.close()
                    break
                if comando:
                    if comando[0] in ["login", "adduser"]:
                        self.socket_ssl.sendall(bytes(entrada, 'ascii'))
                    elif comando[0] == "passwd":
                        if not self.usuario:
                            self.msg_usuario = "Você precisa estar logado para modificar sua senha!"
                        else:
                            self.socket_ssl.sendall(bytes(entrada + ' ' + str(self.usuario), 'ascii'))
                    else:
                        self.socket.sendall(bytes(entrada, 'ascii'))

    # def imprime(self): 
    #     os.system('cls||clear')
    #     print(self.msg_usuario, "\nJogoDaVelha> ", end="")

    def recv_packets(self, sockt):
        while True:
            try:
                data = sockt.recv(1024)
                entrada = [item.decode("utf-8") for item in data.split()]
            except:
                break
            if (entrada[0] == "heartbeat"):
                continue
            elif (entrada[0] == "login"):
                self.login(entrada[1], entrada[2])
            elif (entrada[0] == "adduser"):
                self.adduser(entrada[1])
            elif (entrada[0] == "passwd"):
                self.adduser(entrada[1])
            # self.imprime()
    
    def login(self, status, user):
        if (status == "SUCESSO"):
            self.usuario = user
            self.msg_usuario = "Login realizado com sucesso. Bem vindo " + self.usuario + "!"
        elif (status == "SESSAO_EM_USO"):
            self.msg_usuario = "Falha no login: este usuário já possui uma sessão ativa!"
        elif (status == "ERRO_DE_CREDENCIAIS"):
            self.msg_usuario = "Falha no login: credenciais incorretas!"
        print('\e[A\e[kOutput\nCurrent state of the prompt', end='')
        

    def adduser(self, status):
        if (status == "SUCESSO"):
            self.msg_usuario = "Usuário cadastrado com sucesso!"
        elif (status == "USUARIO_JA_EXISTE"):
            self.msg_usuario = "Já existe um usuário com esse nome!"
        elif (status == "ERRO"):
            self.msg_usuario = "Erro ao conectar ao banco de dados!"

    def passwd(self, status):
        if (status == "SUCESSO"):
            self.msg_usuario = "Senha modificada com sucesso!"
        elif (status == "USUARIO_NAO_LOGADO"):
            self.msg_usuario = "Usuário não logado!"
        elif (status == "SENHA_INCORRETA"):
            self.msg_usuario = "Falha! Por favor verifique as credenciais."
        


def main():
    cliente = Cliente()
    cliente.run()    
            
            


if __name__ == '__main__':
    main()
