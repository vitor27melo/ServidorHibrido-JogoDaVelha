import json
import socket
import ssl
import sys
from threading import Thread, enumerate
from multiprocessing import Process
from time import sleep
import sqlite3
from sqlite3 import Error

# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '127.0.0.1'
TCP_PORT = 4000
TCP_PORT_SSL = 4001
BUFFER_SIZE = 1024
DEBUG = True
class ClientProcess(Process):

    def __init__(self, ip, port, port_ssl, client_sk, client_sk_ssl):
        Process.__init__(self)
        self.ip = ip

        self.port = port
        self.socket = client_sk

        self.port_ssl = port_ssl
        self.socket_ssl = client_sk_ssl

        self.usuario = None
        print("[+] New server socket thread started for " + ip + ":" + str(port))

    def run(self):

        thread_recv =  Thread(daemon=True, target = self.recv_packets, args =(self.socket,))
        thread_recv.start()

        self.socket_ssl = ssl.wrap_socket(self.socket_ssl, server_side=True, keyfile="cert/MyKey.key",
                                     certfile="cert/MyCertificate.crt", ssl_version=ssl.PROTOCOL_TLS)
        thread_recv_encrypted =  Thread(daemon=True, target = self.recv_packets, args =(self.socket_ssl,))
        thread_recv_encrypted.start()

        
        while(True):
            sleep(15)
            try:
                self.socket.sendall(bytes('heartbeat', 'ascii'))
            except:
                pass

    def recv_packets(self, sockt):
        conn_db  = abre_conexao_db("database/database.db")
        
        with sockt:
            while True:
                data = None
                try:
                    data = sockt.recv(1024)
                except:
                    pass
                if not data:
                    break
                entrada = [item.decode("utf-8") for item in data.split()]
                if entrada[0] == "exit":
                    sockt.close()
                    break
                if entrada[0] == "adduser":
                    ret = self.adduser(entrada[1], entrada[2], conn_db)
                    sockt.sendall(bytes(ret, 'ascii'))

                elif entrada[0] == "passwd":
                    ret = self.passwd(entrada[1], entrada[2], conn_db)
                    sockt.sendall(bytes(ret, 'ascii'))

                elif entrada[0] == "login":
                    ret = self.login(entrada[1], entrada[2], conn_db)
                    sockt.sendall(bytes(ret, 'ascii'))

                elif entrada[0] == "list":
                    self.list(conn_db)

                elif entrada[0] == "leaders":
                    self.login(entrada[1], entrada[2], conn_db)
                    
                elif entrada[0] == "begin":
                    self.login(entrada[1], entrada[2])

                elif entrada[0] == "delay":
                    self.login(entrada[1], entrada[2])

                elif entrada[0] == "end":
                    self.login(entrada[1], entrada[2])

                elif entrada[0] == "logout":
                    self.login(entrada[1], entrada[2])

                elif entrada[0] == "exit":
                    self.socket.close()
                    print("Conexão do cliente ", self.ip, " terminada pelo cliente.")
                    break
                sockt.sendall(bytes("sucesso", 'ascii'))
        sys.exit()

    def adduser(self, usuario, senha, conn_db):
        cursor = conn_db.cursor()
        try:
            cursor.execute(f"""SELECT id_usuario FROM usuario WHERE nome = "{usuario}" """)
            result = cursor.fetchall()
        except Error as e:
            print(e)
        if(len(result) > 0):
            print("USUARIO_JA_EXISTE")
            return 'login USUARIO_JA_EXISTE'
        
        try:
            cursor.execute(f"""INSERT INTO usuario(nome, senha) VALUES ("{usuario}", "{senha}") """)
        except Error as e:
            print(e)
            return "adduser ERRO"

        conn_db.commit()
        cursor.close()
        return 'adduser SUCESSO ' + str(usuario)

    def passwd(self, old_passwd, new_passwd, conn_db):
        cursor = conn_db.cursor()
        if not self.usuario:
            return 'passwd USUARIO_NAO_LOGADO'
        try:
            cursor.execute(f"""SELECT id_usuario FROM usuario WHERE nome = "{self.usuario}" AND senha = "{old_passwd}" """)
            result = cursor.fetchall()
        except Error as e:
            print(e)
            return ('passwd ERRO')

        if len(result) == 0:
            return 'passwd SENHA_INCORRETA'
        print("resultado", result)
        try:
            cursor.execute(f"""UPDATE usuario SET senha = "{new_passwd}" WHERE id_usuario = {result[0][0]}""")
        except Error as e:
            print(e)
            return ('passwd ERRO')
        
        conn_db.commit()
        cursor.close()
        return 'passwd SUCESSO'
        

    def login(self, usuario, senha, conn_db):
        cursor = conn_db.cursor()
        try:
            cursor.execute(f"""SELECT id_usuario, nome, status FROM usuario WHERE nome = "{usuario}" AND senha = "{senha}" LIMIT 1""")
            result = cursor.fetchall()
        except Error as e:
            print(e)

        if len(result) == 0:
            print("Não foi encontrado usuário com essas credenciais")
            return ('login ERRO_DE_CREDENCIAIS ' + usuario)
        user = result[0]
        # if (user["status"] == "ativo"):
        if (user[2] == "ativo"):
            print("Esse usuário já possui uma sessão ativa.")
            return ('login SESSAO_EM_USO ' + usuario)
        else:
            try:
                cursor.execute(f"""UPDATE usuario SET status = "ativo" WHERE id_usuario = {user[0]}""")
            except Error as e:
                print(e)
            self.usuario = user[1]
        
        conn_db.commit()
        cursor.close()
        return 'login SUCESSO ' + str(user[1])

    def list(self):
        pass

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
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind((TCP_IP, TCP_PORT))

    tcp_sock_ssl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock_ssl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock_ssl.bind((TCP_IP, TCP_PORT_SSL))

    conn_db  = abre_conexao_db("database/database.db")
    inicia_bd(conn_db)

    while True:
        tcp_sock.listen(4)
        tcp_sock_ssl.listen()
        print("Multithreaded Python server : Waiting for connections from TCP clients...")
        (client_sk, (ip, port)) = tcp_sock.accept()
        (client_sk_ssl, (ip_ssl, port_ssl)) = tcp_sock_ssl.accept()
        newtProcess = ClientProcess(ip, port, port_ssl, client_sk, client_sk_ssl)
        newtProcess.start()

    return 0


if __name__ == '__main__':
    main()
