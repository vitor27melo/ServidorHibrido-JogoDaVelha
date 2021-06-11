import asyncio
import json
import socket
import ssl
import sys
from threading import Thread
from time import sleep
from queue import Queue


# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '127.0.0.1'
TCP_PORT = 4000
BUFFER_SIZE = 1024
DEBUG = True

usuarios = []

class ClientThread(Thread):

    def __init__(self, ip, port, client_sk):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.socket = client_sk
        self.usuario = None
        self.loop = asyncio.get_event_loop()
        print("[+] New server socket thread started for " + ip + ":" + str(port))

    async def read_messages(self):
        with self.socket:
            while True:
                print("read_messages")
                data = self.socket.recv(1024)
                print("data => ", data)
                if not data:
                    break
                entrada = [item.decode("utf-8") for item in data.split()]

                if entrada[0] == "adduser":
                    self.adduser(entrada[1], entrada[2])

                elif entrada[0] == "passwd":
                    self.passwd(entrada[1], entrada[2])

                elif entrada[0] == "login":
                    self.login(entrada[1], entrada[2])

                elif entrada[0] == "leaders":
                    self.login(entrada[1], entrada[2])

                elif entrada[0] == "begin":
                    self.login(entrada[1], entrada[2])

                elif entrada[0] == "delay":
                    self.login(entrada[1], entrada[2])

                elif entrada[0] == "end":
                    self.login(entrada[1], entrada[2])

                elif entrada[0] == "logout":
                    self.login(entrada[1], entrada[2])

                elif entrada[0] == "exit":
                    exit_sucesso = True
                    break
        if not exit_sucesso:
            self.conexao_perdida()
        print("sys.exit")
        sys.exit()

    async def send_messages(self):
        with self.socket:
            while True:
                print("send_messages")
                # await asyncio.sleep(3)
                for i in range(10000000):
                    pass
                print("Enviando heartbeat")
                self.socket.sendall(bytes('heartbeat', 'ascii'))

    async def func(self):
        L = await asyncio.gather(
            self.send_messages(),
            self.read_messages()
        )

        # task1 = asyncio.create_task(self.read_messages())
        # # task2 = asyncio.create_task(self.send_messages())
        # await task1
        # # await task1

    def rodar(self):
        return self.loop.run_until_complete(self.func())

    def adduser(self, name, passwd):
        global usuarios
        usuarios.append({"nome": name, "passwd": passwd})
        if DEBUG:
            print("Lista de usuários: \t", usuarios, "\n")
        pass

    def passwd(self, old_passwd, new_passwd):
        print("passwd")
        pass

    def login(self, name, passwd):
        print("Entrou login")
        # Realiza o wrap no socket e retorna um socket SSL
        socket_ssl = ssl.wrap_socket(self.socket, server_side=True, keyfile="cert/MyKey.key",
                                     certfile="cert/MyCertificate.crt")
        # Recebe as credenciais de forma segura
        credentials = socket_ssl.recv(1024)
        # Realiza o unwrap e retorna um socket comum
        self.socket = socket_ssl.unwrap()
        return True

    def leaders(self):
        pass

    def begin(self):
        pass

    def delay(self):
        print("logout")
        pass

    def end(self):
        print("logout")
        pass

    def logout(self):
        pass

    def exit(self):
        # Atualiza status
        pass

    def conexao_perdida(self):
        # Escreve status no json usuarios
        print("Conexão perdida:", self.ip, self.port)
        return


def daemon_process():
    while True:
        print("Hello")
        sleep(2)


def main():
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server.bind((TCP_IP, TCP_PORT))

    # daemon = Thread(name='daemon_thread', target=daemon_process, daemon=True)
    # daemon.start()

    threads = []

    global usuarios

    # Abre / Cria o arquivo contendo os usuários e senhas 
    with open("usuarios.json") as file_usuarios:
        usuarios = json.load(file_usuarios)

    while True:
        tcp_server.listen(4)
        print("Multithreaded Python server : Waiting for connections from TCP clients...")
        (client_sk, (ip, port)) = tcp_server.accept()
        newthread = ClientThread(ip, port, client_sk)
        newthread.rodar()
        threads.append(newthread)

    # for t in threads:
    #     t.join()

    return 0


if __name__ == '__main__':
    main()
