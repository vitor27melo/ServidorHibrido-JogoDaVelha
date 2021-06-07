import sys
import json
import socket 
import ssl
from threading import Thread

# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '127.0.0.1'
TCP_PORT = 4000 
BUFFER_SIZE = 1024
DEBUG = True

usuarios = None

class ClientThread(Thread): 
 
    def __init__(self,ip,port,client_sk): 
        Thread.__init__(self) 
        self.ip = ip 
        self.port = port
        self.socket = client_sk

        self.usuario = None

        print ("[+] New server socket thread started for " + ip + ":" + str(port)) 
 
    def run(self): 
        exit_sucesso = False
        with self.socket:
            while True: 
                data = self.socket.recv(1024)
                print("data => ", data) 
                if not data:
                    break
                entrada = [item.decode("utf-8") for item in data.split()]

                if(entrada[0] == "adduser"):
                    self.adduser(entrada[1], entrada[2])

                if(entrada[0] == "passwd"):
                    self.passwd(entrada[1], entrada[2])

                if(entrada[0] == "login"):
                    self.login()

                if(entrada[0] == "leaders"):
                    self.login(entrada[1], entrada[2])

                if(entrada[0] == "begin"):
                    self.login(entrada[1], entrada[2])

                if(entrada[0] == "delay"):
                    self.login(entrada[1], entrada[2])

                if(entrada[0] == "end"):
                    self.login(entrada[1], entrada[2])

                if(entrada[0] == "logout"):
                    self.login(entrada[1], entrada[2])

                if(entrada[0] == "exit"):
                    exit_sucesso = True
                    self.login(entrada[1], entrada[2])

                # self.socket.sendall(data)
        if (exit_sucesso == False):
            self.conexao_perdida()
        sys.exit()
    
    def adduser(self, name, passwd):
        global usuarios
        usuarios.append({"nome": name, "passwd": passwd})
        if DEBUG:
            print("Lista de usuários: \t", usuarios, "\n")
        pass

    def passwd(self):
        print("login")
        pass

    def login(self):
        print("Entrou login")
        wrappedSocket = ssl.wrap_socket(self.socket, server_side=True, keyfile="cert/MyKey.key", certfile="cert/MyCertificate.crt")
        credentials = wrappedSocket.recv(1024)
        print("Credenciais", credentials)
        self.socket = wrappedSocket.unwrap()
        print("->",self.socket.recv(1024))
        return



    def leaders():
        pass

    def begin():
        pass

    def delay():
        print("logout")
        pass

    def end():
        print("logout")
        pass

    def logout():
        print("logout")
        pass

    def exit(self):
        # Atualiza status
        pass

    def conexao_perdida(self):
        # Escreve status no json usuarios
        print("Conexão perdida:", self.ip, self.port)
        return

def main():
    tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    tcpServer.bind((TCP_IP, TCP_PORT))
    threads = [] 
    global usuarios
    

    # Abre / Cria o arquivo contendo os usuários e senhas 
    with open("usuarios.json") as file_usuarios:
        usuarios = json.load(file_usuarios)
        file_usuarios.close()

    while True: 
        tcpServer.listen(4) 
        print ("Multithreaded Python server : Waiting for connections from TCP clients...")
        (client_sk, (ip,port)) = tcpServer.accept() 
        newthread = ClientThread(ip,port,client_sk) 
        newthread.start() 
        threads.append(newthread) 

    for t in threads: 
        t.join()
    
    return 0

main() 