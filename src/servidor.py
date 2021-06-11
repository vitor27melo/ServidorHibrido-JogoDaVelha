import json
import socket
import ssl
import sys
from threading import Thread
from time import sleep
import sqlite3
from sqlite3 import Error

# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '127.0.0.1'
TCP_PORT = 4000
BUFFER_SIZE = 1024
DEBUG = True
class ClientThread(Thread):

    def __init__(self, ip, port, client_sk, conn):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.socket = client_sk
        self.conn_bd = conn
        self.usuario = None
        self.sair = False

        print("[+] New server socket thread started for " + ip + ":" + str(port))

    def heartbeat(self):
        while True:
            sleep(5)
            if self.sair:
                sys.exit()
            try:
                # Verificar antes se o socket não está wrapeado em ssl
                self.socket.sendall(bytes('heartbeat', 'ascii'))
            except:
                pass
    def run(self):

        thread_heartbeat =  Thread(target = self.heartbeat, args =())
        thread_heartbeat.start()

        exit_sucesso = False
        with self.socket:
            while True:
                data = None
                try:
                    data = self.socket.recv(1024)
                    print("data => ", data)
                except:
                    pass
                if not data:
                    break
                entrada = [item.decode("utf-8") for item in data.split()]

                if entrada[0] == "adduser":
                    self.adduser(entrada[1], entrada[2])

                elif entrada[0] == "passwd":
                    self.passwd(entrada[1], entrada[2])

                elif entrada[0] == "login":
                    self.login()

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
                    self.sair = True
                    self.socket.close()
                    print("Conexão do cliente ", self.ip, " terminada pelo cliente.")
                    break
                self.socket.sendall(data)
        self.sair = True
        if not exit_sucesso:
            self.conexao_perdida()
        sys.exit()

    def adduser(self, name, passwd):
        pass
        # global usuarios
        # usuarios.append({"nome": name, "passwd": passwd})
        # if DEBUG:
        #     print("Lista de usuários: \t", usuarios, "\n")
        # pass

    def passwd(self, old_passwd, new_passwd):
        print("passwd")
        pass

    def login(self):
        print("Entrou login")
        # Realiza o wrap no socket e retorna um socket SSL
        socket_ssl = ssl.wrap_socket(self.socket, server_side=True, keyfile="cert/MyKey.key",
                                     certfile="cert/MyCertificate.crt", ssl_version=ssl.PROTOCOL_TLS_SERVER)
        # socket_ssl = ssl.wrap_socket(self.socket, server_side=True, keyfile="cert/MyKey.key",
        #                              certfile="cert/MyCertificate.crt", ssl_version=ssl.PROTOCOL_TLS_SERVER)
        # Recebe as credenciais de forma segura
        credentials = socket_ssl.recv(1024)
        print("Credentials: ", credentials)
        # Realiza o unwrap e retorna um socket comum
        self.socket = socket_ssl.unwrap()

        cursor = self.conn_bd.cursor()
        query = f"""
            SELECT * FROM usuario WHERE nome = {credentials[0]} AND senha = {credentials[1]} LIMIT 1 
        """
        try:
            cursor.execute(query)
            print(cursor.fetchall())
        except Error as e:
            print(e)
            

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
        print("Conexão perdida:", self.ip, self.port)
        return

def abre_conexao_db(path):
    conn = None
    try:
        conn = sqlite3.connect(path)
        return conn
    except Error as e:
        print(e)
    return conn

def inicia_bd(conn):
    cursor = conn.cursor()

    sql_create_projects_table = f"""
        CREATE TABLE IF NOT EXISTS usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nome varchar(50) NOT NULL,
            senha varchar(50) NOT NULL,
            status varchar(10) NOT NULL DEFAULT "inativo"
        );
    """
    try:
        cursor.execute(sql_create_projects_table)
    except Error as e:
        print(e)

    cursor.close()
    conn.commit()
    conn.close()

def main():
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server.bind((TCP_IP, TCP_PORT))

    threads = []

    conn  = abre_conexao_db("database/database.db")
    inicia_bd(conn)

    while True:
        tcp_server.listen(4)
        print("Multithreaded Python server : Waiting for connections from TCP clients...")
        (client_sk, (ip, port)) = tcp_server.accept()
        newthread = ClientThread(ip, port, client_sk, conn)
        newthread.start()
        threads.append(newthread)

    # for t in threads:
    #     t.join()

    return 0


if __name__ == '__main__':
    main()
