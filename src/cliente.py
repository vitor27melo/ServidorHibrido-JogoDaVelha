#!/usr/bin/env python3
from threading import Thread
import sys
import json
import socket
import ssl
import os
from time import sleep
from queue import Queue


HOST = '127.0.0.1'  # The server's hostname or IP address

class Cliente():
    def __init__(self, port, port_ssl, port_p2p):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_ssl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, port))
        self.socket_ssl.connect((HOST, port_ssl))
        self.socket_ssl = ssl.wrap_socket(self.socket_ssl, ssl_version=ssl.PROTOCOL_TLS)
        self.port_p2p = port_p2p
        self.usuario = None
        self.msg_usuario = ''
        self.busy_printing = False

    def run(self):
        with self.socket:
            queue = Queue()
            thread_print = Thread(target = self.imprime, args=(queue,))
            thread_print.start()

            thread_recv =  Thread(target = self.recv_packets, args=(self.socket, queue))
            thread_recv.start()

            thread_recv_encrypted =  Thread(target = self.recv_packets, args=(self.socket_ssl, queue))
            thread_recv_encrypted.start()

            while True:
                entrada = input("")
                queue.put("limpar")
                comando = entrada.split()
                if entrada == "exit":
                    self.socket_ssl.sendall(bytes(entrada, 'ascii'))
                    self.socket.sendall(bytes(entrada, 'ascii'))
                    self.socket.close()
                    break
                if comando:
                    if comando[0] in ["passwd", "logout", "begin"] and not self.usuario:
                        queue.put("Você precisa estar logado para executar esta ação!")
                    elif comando[0] == "begin" and comando[1] == self.usuario:
                        queue.put("Seu engraçadinho, você não pode se convidar para uma partida.")
                    elif comando[0] in ["login", "adduser", "passwd"]:
                        self.socket_ssl.sendall(bytes(entrada, 'ascii'))
                    else:
                        self.socket.sendall(bytes(entrada + ' ' + str(self.port_p2p) if comando[0] == "begin" else entrada, 'ascii'))


    def imprime(self, queue):
        mensagem = ""
        print("JogoDaVelha> ", end="")
        while True:
            data = queue.get()
            if (data == "limpar"):
                mensagem = ""
            elif (data != ""):
                mensagem = data
            os.system('cls||clear')
            print(mensagem, "\nJogoDaVelha> ", end="")
 
    def recv_packets(self, sockt, queue):
        while True:
            message = ""
            try:
                data = sockt.recv(1024)
                entrada = [item.decode("utf-8") for item in data.split()]
            except:
                break
            if (entrada[0] == "heartbeat"):
                continue
            elif (entrada[0] == "login"):
                message = self.login(entrada[1], entrada[2])
            elif (entrada[0] == "logout"):
                message = self.logout(entrada[1])
            elif (entrada[0] == "adduser"):
                message = self.adduser(entrada[1])
            elif (entrada[0] == "passwd"):
                message = self.adduser(entrada[1])
            elif (entrada[0] == "list"):
                message = self.list(entrada[1], entrada[2])
            elif (entrada[0] == "begin"):
                queue.put(self.begin(entrada[1], entrada[2]))
                if entrada[1] == "SUCESSO":
                    self.escuta_p2p(entrada[1], queue)

            queue.put(message)
    
    def login(self, status, user):
        if (status == "SUCESSO"):
            self.usuario = user
            return "Login realizado com sucesso. Bem vindo " + self.usuario + "!"
        elif (status == "SESSAO_EM_USO"):
            return "Falha no login: este usuário já possui uma sessão ativa!"
        elif (status == "ERRO_DE_CREDENCIAIS"):
            return "Falha no login: credenciais incorretas!"

    def logout(self, status):
        if (status == "SUCESSO"):
            self.usuario = None
            return "Logout realizado com sucesso!"
        elif (status == "ERRO"):
            return "Falha ao fazer logout!"

    def adduser(self, status):
        if (status == "SUCESSO"):
            return "Usuário cadastrado com sucesso!"
        elif (status == "USUARIO_JA_EXISTE"):
            return "Já existe um usuário com esse nome!"
        elif (status == "ERRO"):
            return "Erro ao conectar ao banco de dados!"

    def passwd(self, status):
        if (status == "SUCESSO"):
            return "Senha modificada com sucesso!"
        elif (status == "USUARIO_NAO_LOGADO"):
            return "Usuário não logado!"
        elif (status == "SENHA_INCORRETA"):
            return "Falha! Por favor verifique as credenciais."
    
    def list(self, status, lista):
        mensagem = "\033[1mNome\t\tStatus\t\tEm partida com\033[0m\n"
        if (status == "ERRO"):
            return "Falha ao recuperar lista de usuários."
        elif (status == "SUCESSO"):
            a = json.loads(lista)
            for item in a:
                mensagem = mensagem + item[0] + '\t\t' + item[1] + '\t\t' + item[2] + '\n'
            return mensagem
    
    def begin(self, status, usuario_convidado):
        if status == "SUCESSO":
            # Iniciar escuta
            return 'Esperando resposta do usuário ' + usuario_convidado + ' (tempo máximo de espera: 20s).'
        elif status == "USUARIO_NAO_ENCONTRADO":
            return 'O usuário ' + usuario_convidado + ' não foi encontrado.'
        elif status == "USUARIO_NAO_ATIVO":
            return 'O usuário ' + usuario_convidado + ' não está ativo no momento.'
        elif status == "USUARIO_EM_PARTIDA":
            return 'O usuário ' + usuario_convidado + ' já está em uma partida.'
        elif status == "ERRO":
            return 'Falha ao convidar o usuário ' + usuario_convidado + '.'
        
    def escuta_p2p(self, adversario, queue):
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_sock.settimeout(20)
        tcp_sock.bind((HOST, self.port_p2p))
        tcp_sock.listen(4)
        try:
            (client_sk, (ip, port)) = tcp_sock.accept()
        except socket.timeout:
            queue.put("Infelizmente o usuário " + adversario + " não respondeu ao seu convite.")




def main():
    PORT = int(sys.argv[1])
    PORT_SSL = int(sys.argv[2])
    PORT_P2P = int(sys.argv[3])
    cliente = Cliente(PORT, PORT_SSL, PORT_P2P)
    cliente.run()    
            
            


if __name__ == '__main__':
    main()
