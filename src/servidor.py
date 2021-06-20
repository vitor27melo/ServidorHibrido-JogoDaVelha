#!/usr/bin/env python3
import json
import socket
import ssl
import sys
from threading import Thread, enumerate
from multiprocessing import Process
from time import sleep
import sqlite3
from sqlite3 import Error
from datetime import datetime

FREQ_HEARTBEAT = 5 # Frequência (em segundos) na qual pacotes heartbeat são enviados para um cliente

def log(msg):
    try:
        file = open("log.txt", "a+")
        file.write(datetime.now().strftime("%d/%m/%Y@%H:%M:%S") + " => " + msg + "\n")
        file.close()
    except:
        log(msg)

class ClientProcess(Process):

    def __init__(self, ip, port, port_ssl, client_sk, client_sk_ssl):
        Process.__init__(self)
        self.heartbeats_nao_respondidos = 0
        self.finalizar_cliente = False

        self.ip = ip

        self.port = port
        self.socket = client_sk

        self.port_ssl = port_ssl
        self.socket_ssl = client_sk_ssl

        self.usuario = None
        self.em_partida = False

        self.id_convite_enviado_bd = None
        self.convite_recebido = None
        log(f"""Novo cliente conectado pelo IP {ip}: {str(port)} e {str(port_ssl)}""")

    def run(self):

        thread_recv = Thread(daemon=True, target = self.recv_packets, args =(self.socket,))
        thread_recv.start()

        self.socket_ssl = ssl.wrap_socket(self.socket_ssl, server_side=True, keyfile="certificates/MyKey.key",
                                     certfile="certificates/MyCertificate.crt", ssl_version=ssl.PROTOCOL_TLS)
        thread_recv_encrypted = Thread(daemon=True, target = self.recv_packets, args =(self.socket_ssl,))
        thread_recv_encrypted.start()

        thread_invitation = Thread(daemon=True, target = self.check_invitations, args =(self.socket,))
        thread_invitation.start()

        conn_db  = abre_conexao_db("database/database.db")
        while(True):
            sleep(FREQ_HEARTBEAT)
            if self.finalizar_cliente:
                break
            self.heartbeats_nao_respondidos += 1
            if self.heartbeats_nao_respondidos >= 3:
                log(f"""O cliente de IP {self.ip} econtra-se irresponsivo (heartbeats) e será finalizado!""")
                self.exit(conn_db)
                sys.exit()
            try:
                self.socket.sendall(bytes('heartbeat', 'ascii'))
            except:
                pass
        sys.exit()

    def check_invitations(self, sockt):
        conn_db  = abre_conexao_db("database/database.db")
        cursor = conn_db.cursor()
        while(True):
            if self.usuario and not self.id_convite_enviado_bd and not self.convite_recebido:
                cursor.execute(f"""SELECT * FROM convite WHERE convidado = "{self.usuario}" AND status = "pendente" LIMIT 1""")
                result = cursor.fetchall()
                if len(result) > 0:
                    print("convite recebido")
                    self.convite_recebido = result[0]
                    sockt.sendall(bytes('convite ' + self.convite_recebido[1],'ascii'))
            sleep(1)

    def recv_packets(self, sockt):
        conn_db  = abre_conexao_db("database/database.db")
        
        with sockt:
            while True:
                try:
                    data = None
                    data = sockt.recv(1024)

                    if not data:
                        break
                    entrada = [item.decode("utf-8") for item in data.split()]
                    if entrada[0] == "heartbeat":
                        self.heartbeats_nao_respondidos = 0

                    elif entrada[0] == "adduser":
                        ret = self.adduser(entrada[1], entrada[2], conn_db)
                        sockt.sendall(bytes(ret, 'ascii'))
                        
                    elif entrada[0] == "passwd":
                        ret = self.passwd(entrada[1], entrada[2], conn_db)
                        sockt.sendall(bytes(ret, 'ascii'))

                    elif entrada[0] == "login":
                        ret = self.login(entrada[1], entrada[2], conn_db)
                        sockt.sendall(bytes(ret, 'ascii'))

                    elif entrada[0] == "logout":
                        ret = self.logout(entrada[1], conn_db)
                        sockt.sendall(bytes(ret, 'ascii'))

                    elif entrada[0] == "list":
                        ret = self.list(conn_db)
                        sockt.sendall(bytes(ret, 'ascii'))

                    elif entrada[0] == "leaders":
                        ret = self.leaders(conn_db)
                        sockt.sendall(bytes(ret, 'ascii'))
                        
                    elif entrada[0] == "begin":
                        ret = self.begin(entrada[1], entrada[2], entrada[3], conn_db)
                        sockt.sendall(bytes(ret, 'ascii'))

                    elif entrada[0] == "S": # Aceitando convite
                        ret = self.aceita_convite(conn_db)
                        sockt.sendall(bytes(ret, 'ascii'))

                    elif entrada[0] == "N": 
                        ret = self.recusa_convite(conn_db)
                        sockt.sendall(bytes(ret, 'ascii'))

                    elif entrada[0] == "cancela_convite":
                        ret = self.cancela_convite(conn_db)

                    elif entrada[0] == "jogo_iniciado":
                        ret = self.jogo_iniciado(entrada[1], entrada[2], entrada[3], conn_db)

                    elif entrada[0] == "resultado":
                        ret = self.resultado(entrada[1], entrada[2], entrada[3], entrada[4], entrada[5], conn_db)

                    elif entrada[0] == "end":
                        self.end(conn_db)

                    elif entrada[0] == "exit":
                        self.finalizar_cliente = True
                        self.exit(conn_db)
                        print("Conexão do cliente ", self.ip, " terminada pelo cliente.")
                        break
                except:
                    continue
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
            log(f"""Cliente de IP {self.ip}  tentou realizar o login com usuário ({usuario}), mas as credenciais estavam incorretas""")
            return ('login ERRO_DE_CREDENCIAIS ' + usuario)
        user = result[0]
        if (user[2] == "ativo"):
            log(f"""Cliente de IP {self.ip} tentou realizar o login com usuário ({usuario}), mas já havia uma sessão ativa""")
            return ('login SESSAO_EM_USO ' + usuario)
        else:
            try:
                cursor.execute(f"""UPDATE usuario SET status = "ativo" WHERE id_usuario = {user[0]}""")
            except Error as e:
                print(e)
            self.usuario = user[1]
        
        conn_db.commit()
        cursor.close()
        log(f"""Cliente de IP {self.ip} realizou o login com usuário ({usuario}) com sucesso.""")
        return 'login SUCESSO ' + str(user[1])

    def logout(self, usuario, conn_db):
        if usuario != self.usuario:
            return 'logout ERRO'
        cursor = conn_db.cursor()
        try:
            cursor.execute(f"""UPDATE usuario SET status = "inativo", em_partida_com = "Ninguém" WHERE nome = "{usuario}" """)
        except Error as e:
            print(e)
            return 'logout ERRO'
        self.usuario = None
        conn_db.commit()
        cursor.close()
        return 'logout SUCESSO'

    def list(self, conn_db):
        cursor = conn_db.cursor()
        try:
            cursor.execute(f"""SELECT nome, status, em_partida_com FROM usuario""")
            result = cursor.fetchall()
        except Error as e:
            print(e)
            return ('list ERRO')

        cursor.close()
        return 'list SUCESSO ' + str(json.dumps(result).replace(" ", ""))

    def leaders(self, conn_db):
        cursor = conn_db.cursor()
        try:
            cursor.execute(f"""SELECT nome, vitorias, derrotas, empates FROM usuario ORDER BY vitorias DESC""")
            result = cursor.fetchall()
        except Error as e:
            print(e)
            return ('leaders ERRO')

        cursor.close()
        return 'leaders SUCESSO ' + str(json.dumps(result).replace(" ", ""))

    def begin(self, usuario_a_convidar, ip_p2p, porta_p2p, conn_db):
        cursor = conn_db.cursor()
        try:
            cursor.execute(f"""SELECT nome, status, em_partida_com FROM usuario WHERE nome = "{usuario_a_convidar}" """)
            result = cursor.fetchall()
        except Error as e:
            print(e)
            return 'begin ERRO ' + str(usuario_a_convidar)  + ' 0'

        if len(result) == 0:
            return 'begin USUARIO_NAO_ENCONTRADO ' + str(usuario_a_convidar) + ' 0'

        user = result[0]
        if user[1] == "inativo":
            return 'begin USUARIO_NAO_ATIVO ' + str(usuario_a_convidar) + ' 0'

        if user[2] != "Ninguém":
            return 'begin USUARIO_EM_PARTIDA ' + str(usuario_a_convidar) + ' 0'

        try:
            cursor.execute(f"""
                INSERT INTO convite (convidante, convidado, ip_convidante, porta_convidante)
                VALUES ("{self.usuario}", "{usuario_a_convidar}", "{ip_p2p}", "{porta_p2p}")
            """)
            self.id_convite_enviado_bd = cursor.lastrowid
        except Error as e:
            print(e)
            return 'begin ERRO ' + str(usuario_a_convidar)  + ' 0'
        
        conn_db.commit()
        cursor.close()
        return 'begin SUCESSO ' + str(usuario_a_convidar) + ' ' + str(self.id_convite_enviado_bd)

    def aceita_convite(self, conn_db):
        cursor = conn_db.cursor()
        try:
            cursor.execute(f"""UPDATE convite SET status = "aceito" WHERE id_convite = "{self.convite_recebido[0]}" """)
        except Error as e:
            print(e)
            return 'inicia_jogo ERRO '
        conn_db.commit()
        cursor.close()
        return 'inicia_jogo ' + self.convite_recebido[1] + ' ' + self.convite_recebido[3] + ' ' + self.convite_recebido[4]

    def cancela_convite(self, conn_db):
        cursor = conn_db.cursor()
        try:
            cursor.execute(f"""UPDATE convite SET status = "cancelado" WHERE id_convite = {self.id_convite_enviado_bd} """)
            self.id_convite_enviado_bd = None
        except Error as e:
            print(e)

        conn_db.commit()
        cursor.close()
        return

    def jogo_iniciado(self, convidante, convidado, id_convite, conn_db):

        cursor = conn_db.cursor()
        try:
            cursor.execute(f"""UPDATE convite SET status = "jogo_iniciado" WHERE id_convite = {id_convite} """)
            cursor.execute(f"""UPDATE usuario SET em_partida_com = "{convidante}" WHERE nome = "{convidado}" """)
            cursor.execute(f"""UPDATE usuario SET em_partida_com = "{convidado}" WHERE nome = "{convidante}" """)
        except Error as e:
            print(e)
        conn_db.commit()
        cursor.close()
        log(f"""Partida iniciada entre os jogadores {convidado} e {convidante}""")
        return
    
    def resultado(self, id_convite, vitorioso, derrotado, ip_vitorioso, ip_derrotado, conn_db):
        cursor = conn_db.cursor()
        try: 
            cursor.execute(f"""SELECT status FROM convite WHERE id_convite = {id_convite} """)
            retorno = cursor.fetchall()[0]
            if retorno[0] == 'jogo_iniciado':
                cursor.execute(f"""UPDATE convite SET status = "finalizado" WHERE id_convite = {id_convite} """)
                cursor.execute(f"""UPDATE usuario SET em_partida_com = "Ninguém" WHERE nome = "{vitorioso}" OR nome = "{derrotado}" """)
                if (vitorioso == "empate"):
                    cursor.execute(f"""UPDATE usuario SET empates = empates + 1 WHERE nome = "{vitorioso}" OR nome = "{derrotado}" """)
                    log(f"""Partida finalizada. O jogador {vitorioso} (IP {ip_vitorioso}) empatou com o jogador {derrotado} (IP {ip_derrotado})""")
                else:
                    log(f"""Partida finalizada. O jogador {vitorioso} (IP {ip_vitorioso}) venceu o jogador {derrotado} (IP {ip_derrotado})""")
                    cursor.execute(f"""UPDATE usuario SET vitorias = vitorias + 1 WHERE nome = "{vitorioso}" """)
                    cursor.execute(f"""UPDATE usuario SET derrotas = derrotas + 1 WHERE nome = "{derrotado}" """)
                self.em_partida = False
                self.id_convite_enviado_bd = None
                self.convite_recebido = None
        except Error as e:
            print(e)
        conn_db.commit()
        cursor.close()
        return

    def end(self, conn_db):
        cursor = conn_db.cursor()
        if self.id_convite_enviado_bd:
            try:
                cursor.execute(f"""UPDATE convite SET status = "Jogo Cancelado" WHERE id_convite = {self.id_convite_enviado_bd}""")
            except Error as e:
                print(e)
        else:
            return "O seu adversário forçou o encerramento antecipado da partida."
        return True

    def exit(self, conn_db):
        if self.usuario:
            cursor = conn_db.cursor()
            cursor.execute(f"""UPDATE usuario SET status = "inativo", em_partida_com = "Ninguém" WHERE nome = "{self.usuario}" """)
            conn_db.commit()
            cursor.close()
        print("Conexão com cliente de IP = " + self.ip + " encerrada.")
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

    table_usuario = f"""
        CREATE TABLE IF NOT EXISTS usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nome varchar(50) UNIQUE NOT NULL,
            senha varchar(50) NOT NULL,
            status varchar(10) NOT NULL DEFAULT "inativo",
            em_partida_com varchar(50) DEFAULT "Ninguém",
            vitorias INTEGER DEFAULT 0,
            derrotas INTEGER DEFAULT 0,
            empates INTEGER DEFAULT 0
        );
    """

    table_convite = f"""
        CREATE TABLE IF NOT EXISTS convite (
            id_convite INTEGER PRIMARY KEY AUTOINCREMENT,
            convidante varchar(50)  NOT NULL,
            convidado varchar(50) NOT NULL,
            ip_convidante varchar(50) NOT NULL,
            porta_convidante varchar(50) NOT NULL,
            dt_convite datetime DEFAULT current_timestamp,
            status varchar(10) NOT NULL DEFAULT "pendente"
        );
    """
    cursor.execute(table_usuario)
    cursor.execute(table_convite)
    cursor.close()
    conn.commit()
    conn.close()

def main():
    log("Servidor iniciado.")

    TCP_IP = '0.0.0.0'

    try:
        TCP_PORT = int(sys.argv[1])
        TCP_PORT_SSL = int(sys.argv[2])
    except Exception as e:
        print("Passe como parâmetros uma porta para conexões por texto simples e uma para conexões seguras.")
        print("Exemplo: python servidor.py 5000 5001")
        sys.exit()

    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_sock.bind((TCP_IP, TCP_PORT))
    except Exception as e:
        print("Erro ao iniciar socket de conexões com os clientes: ", e)
        sys.exit()

    try:
        tcp_sock_ssl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock_ssl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_sock_ssl.bind((TCP_IP, TCP_PORT_SSL))
    except Exception as e:
        print("Erro ao iniciar socket de conexões seguras com os clientes: ", e)
        sys.exit()

    try:
        conn_db  = abre_conexao_db("database/database.db")
        inicia_bd(conn_db)
    except Error as e:
        print("Não foi possível iniciar a base de dados:", e)
        sys.exit()

    while True:
        tcp_sock.listen(4)
        tcp_sock_ssl.listen()
        print("Esperando por conexões de clientes da rede local nas portas " + str(TCP_PORT) + " e " + str(TCP_PORT_SSL) + "...")
        try:
            (client_sk, (ip, port)) = tcp_sock.accept()
            (client_sk_ssl, (ip_ssl, port_ssl)) = tcp_sock_ssl.accept()
        except Exception as e:
            print("Erro ao iniciar conexões com um cliente: ", e)
        
        try:
            newtProcess = ClientProcess(ip, port, port_ssl, client_sk, client_sk_ssl)
            newtProcess.start()
        except Exception as e:
            print("Erro ao iniciar a thread do cliente de endereço IP ", ip, ": ", e)

if __name__ == '__main__':
    main()
