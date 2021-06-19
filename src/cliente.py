#!/usr/bin/env python3
from threading import Thread
import sys
import json
import socket
import ssl
import os
from time import sleep
from queue import Queue
import timeit

FREQ_DELAY = 5 # Frequência (em segundos) na qual pacotes delay são enviados para o adversário

CASA_VAZIA = 0 # A casa está vazia
CONVIDANTE = 1 # O jogador é representado pela marcação X
CONVIDADO = 2    # O robô (jogador) é representado pela marcação O

class Cliente():
    def __init__(self, host, port, port_ssl, port_p2p):
        self.time_envio_delay = None
        self.delay = []

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

        self.socket_ssl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_ssl.connect((host, port_ssl))
        self.socket_ssl = ssl.wrap_socket(self.socket_ssl, ssl_version=ssl.PROTOCOL_TLS)

        self.port_p2p = port_p2p
        self.socket_p2p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.ip_p2p = socket.gethostbyname(socket.gethostname())  

        self.usuario = None
        self.id_convite_enviado = '0'

        self.tabuleiro = [[CASA_VAZIA for x in range(3)] for y in range(3)]
        self.minha_peca = None # CONVIDADO OU CONVIDANTE
        self.em_jogo = False
        self.meu_turno = False
        self.adversario_atual = None
        self.status_jogo_atual = None

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
                    self.socket_ssl.close()
                    self.socket_p2p.close()
                    break
                if comando:
                    # Comandos DURANTE uma partida
                    if comando[0] in ["send", "delay", "end"]:
                        if comando[0] == "delay":
                            queue.put(self.imprime_latencia())
                        elif not self.em_jogo:
                            queue.put("Você precisa estar em jogo para executar esta ação!")
                        elif comando[0] == "send":
                            if not self.meu_turno:
                                queue.put(self.imprime_tabuleiro("Espere seu adversário realizar sua jogada!"))
                            else:
                                self.socket_p2p.sendall(bytes(entrada, 'ascii'))
                        elif comando[0] == "end":
                            self.socket.sendall(bytes(entrada, 'ascii'))
                            self.socket_p2p.sendall(bytes(entrada, 'ascii'))
                            self.termina_partida()
                    # Comandos para o servidor em que é necessário estar logado
                    elif comando[0] in ["passwd", "logout", "begin"] and not self.usuario:
                        queue.put("Você precisa estar logado para executar esta ação!")
                    elif comando[0] == "begin" and comando[1] == self.usuario:
                        queue.put("Seu engraçadinho, você não pode se convidar para uma partida.")
                    elif comando[0] in ["login", "adduser", "passwd"]:
                        self.socket_ssl.sendall(bytes(entrada, 'ascii'))
                    else:
                        self.socket.sendall(bytes(entrada + ' ' + str(self.ip_p2p) + ' ' + str(self.port_p2p) if comando[0] == "begin" else entrada, 'ascii'))

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
    
    def imprime_tabuleiro(self, msg_inicial = ''):
        print_tabuleiro = msg_inicial + '\n'
        print_tabuleiro += '-------- Tabuleiro Atual --------\n\n'
        for index, linha in enumerate(self.tabuleiro):
            print_tabuleiro += '           '
            print_tabuleiro += 'X | ' if linha[0] == CONVIDANTE else 'O | ' if linha[0] == CONVIDADO else '  | ' 
            print_tabuleiro += 'X | ' if linha[1] == CONVIDANTE else 'O | ' if linha[1] == CONVIDADO else '  | ' 
            print_tabuleiro += 'X | ' if linha[2] == CONVIDANTE else 'O | ' if linha[2] == CONVIDADO else '    '
            print_tabuleiro += '\n'
            if index < 2:
                    print_tabuleiro += '          --- --- ---\n'
        print_tabuleiro +='\n---------------------------------\n\n'
        return print_tabuleiro

    def imprime_latencia(self):
        if len(self.delay) == 0:
            return "Ainda não foram medidos valores de latência para seu adversário."
        elif len(self.delay) == 1:
            return "Últimos valores medidos: " + str(self.delay[-1]/1000)[0:5] + "ms"
        elif len(self.delay) == 2:
            return "Últimos valores medidos: " + str(self.delay[-1]/1000)[0:5] + "ms, " + str(self.delay[-2]/1000)[0:5] + "ms"
        else:
            return "Últimos valores medidos: " + str(self.delay[-1]/1000)[0:5] + "ms, " + str(self.delay[-2]/1000)[0:5] + "ms, " + str(self.delay[-3]/1000)[0:5] + "ms"


    def recv_packets(self, sockt, queue):
        while True:
            message = ""
            try:
                data = sockt.recv(1024)
                entrada = [item.decode("utf-8") for item in data.split()]
            except:
                break
            # COMANDO VINDOS DO ADVERSARIO (P2P)
            if (entrada[0] == "send"):
                if self.send(entrada[1], entrada[2]):
                    self.socket_p2p.sendall(bytes("confirm_send " + entrada[1] + " " + entrada[2], 'ascii'))
                    self.meu_turno = True
                    message = self.imprime_tabuleiro('É a sua vez de jogar.')
            elif (entrada[0] == "confirm_send"):
                if self.confirm_send(entrada[1], entrada[2]):
                    self.meu_turno = False
                    message = self.imprime_tabuleiro('É a vez do seu adversário jogar.')
            elif entrada[0] in ["send", "confirm_send"]:
                result_msg, result = self.verifica_vitoria()
                if result_msg:
                    self.socket.sendall(bytes(result_msg, 'ascii'))
                    if result == 'vitoria':
                        message = self.imprime_tabuleiro('Parabéns! Você venceu a partida!')
                    if result == 'derrota':
                        message = self.imprime_tabuleiro('Derrota! O seu adversário venceu a partida!')
                    if result == 'empate':
                        message = self.imprime_tabuleiro('O jogo terminou em empate!')
                    self.termina_partida()
            elif entrada[0] == "delay_ret":
                self.delay.append(self.time_envio_delay - timeit.timeit())
            elif entrada[0] == "delay":
                self.socket_p2p.sendall(bytes("delay_ret", 'ascii'))
                continue
            elif entrada[0] == "end":
                message = "O seu adversário forçou o encerramento antecipado da partida."
                self.termina_partida()
                continue
            # COMANDOS VINDOS DO SERVIDOR
            elif (entrada[0] == "heartbeat"):
                self.socket.sendall(bytes("heartbeat", 'ascii'))
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
            elif (entrada[0] == "leaders"):
                message = self.leaders(entrada[1], entrada[2])
            elif (entrada[0] == "begin"):
                queue.put(self.begin(entrada[1], entrada[2], entrada[3]))
                if entrada[1] == "SUCESSO":
                    if not self.escuta_p2p(entrada[2], queue):
                        self.socket.sendall(bytes("cancela_convite", 'ascii'))
                    else:
                        self.socket.sendall(bytes("jogo_iniciado " + str(self.usuario) + ' ' + str(self.adversario_atual) + ' ' + str(self.id_convite_enviado), 'ascii'))
                        message = self.imprime_tabuleiro('Jogo iniciado, sua peça é "X". É sua vez de jogar.')
            elif (entrada[0] == "convite"):
                message = self.convite(entrada[1])
            elif (entrada[0] == "inicia_jogo"):
                self.conecta_p2p(entrada[1], entrada[2], entrada[3], queue)
                message = self.imprime_tabuleiro('Jogo iniciado, sua peça é "O". É a vez do seu adversário jogar.')

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
    def leaders(self, status, lista):
        mensagem = "\033[1mNome\t\tVitórias\tDerrotas\tEmpates\033[0m\n"
        if (status == "ERRO"):
            return "Falha ao recuperar placar de classificações."
        elif (status == "SUCESSO"):
            a = json.loads(lista)
            for item in a:
                mensagem = mensagem + str(item[0]) + '\t\t' + str(item[1]) + '\t\t' + str(item[2]) + '\t\t' + str(item[3]) + '\n'
            return mensagem
    
    def begin(self, status, usuario_convidado, id_convite_enviado):
        if status == "SUCESSO":
            self.id_convite_enviado = id_convite_enviado
            # Iniciar escuta
            return 'Esperando resposta do usuário ' + usuario_convidado + ' (tempo máximo de espera: 30s).'
        elif status == "USUARIO_NAO_ENCONTRADO":
            return 'O usuário ' + usuario_convidado + ' não foi encontrado.'
        elif status == "USUARIO_NAO_ATIVO":
            return 'O usuário ' + usuario_convidado + ' não está ativo no momento.'
        elif status == "USUARIO_EM_PARTIDA":
            return 'O usuário ' + usuario_convidado + ' já está em uma partida.'
        elif status == "ERRO":
            return 'Falha ao convidar o usuário ' + usuario_convidado + '.'
        
    def convite(self, adversario):
        return 'O usuário ' + adversario + ' te convidou para uma partida, deseja aceitar? (S/N)'

    def conecta_p2p(self, adversario, ip, porta, queue):
        queue.put("Conenctando: " + ip + porta)
        try:
            self.socket_p2p.connect((ip, int(porta)))
        except:
            queue.put("Erro inesperado. Não foi possível conectar-se com " + adversario + ".")
            return False
        self.adversario_atual = adversario
        self.minha_peca = CONVIDADO
        self.meu_turno = False
        self.em_jogo = True
        thread_recv =  Thread(target = self.recv_packets, args=(self.socket_p2p, queue))
        thread_recv.start()
        thread_delay = Thread(target = self.send_delay, args=())
        thread_delay.start()
        return True

    def escuta_p2p(self, adversario, queue):
        self.socket_p2p.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_p2p.settimeout(30)
        self.socket_p2p.bind(('0.0.0.0', self.port_p2p))
        self.socket_p2p.listen(4)
        try:
            (client_sk, (ip, port)) = self.socket_p2p.accept()
            self.socket_p2p.close()
            self.socket_p2p = client_sk
        except socket.timeout:
            queue.put("Infelizmente o usuário " + adversario + " não respondeu ao seu convite.")
            return False

        self.adversario_atual = adversario
        self.minha_peca = CONVIDANTE
        self.meu_turno = True
        self.em_jogo = True
        thread_recv =  Thread(target = self.recv_packets, args=(self.socket_p2p, queue))
        thread_recv.start()
        thread_delay = Thread(target = self.send_delay, args=())
        thread_delay.start()
        return True
    
    def send_delay(self):
        while(True):
            try:
                self.time_envio_delay = timeit.timeit()
                self.socket_p2p.sendall(bytes('delay', 'ascii'))
            except:
                pass
            sleep(FREQ_DELAY)

    def send(self, linha, coluna):
        # Jogada do adversário
        if (self.tabuleiro[int(linha)][int(coluna)] != CASA_VAZIA):
            return False
        else:
            self.tabuleiro[int(linha)][int(coluna)] = CONVIDADO if self.minha_peca == CONVIDANTE else CONVIDANTE
        return True
    
    def confirm_send(self, linha, coluna):
        # Confirmação da sua jogada
        self.tabuleiro[int(linha)][int(coluna)] = CONVIDANTE if self.minha_peca == CONVIDANTE else CONVIDADO
        return True

    def verifica_vitoria(self):
        contador = 0
        casas_marcadas_D = 0
        casas_marcadas_D_inversa = 0
        for i in range(3):
            casas_marcadas_V = 0
            casas_marcadas_H = 0
            for j in range(3):
                if self.tabuleiro[i][j] != CASA_VAZIA:
                    contador += 1
                if self.tabuleiro[j][i] == CONVIDANTE:
                    casas_marcadas_V += 1
                if self.tabuleiro[i][j] == CONVIDANTE:
                    casas_marcadas_H += 1
            if casas_marcadas_H == 3 or casas_marcadas_V == 3:
                if self.minha_peca == CONVIDANTE:
                    return 'resultado ' + self.id_convite_enviado + ' ' + self.usuario + ' ' + self.adversario_atual, 'vitoria'
                else:
                    return 'resultado ' + self.id_convite_enviado + ' ' + self.adversario_atual + ' ' + self.usuario, 'derrota'
            if self.tabuleiro[i][i] == CONVIDANTE:
                casas_marcadas_D += 1
            if self.tabuleiro[i][2-i] == CONVIDANTE:
                casas_marcadas_D_inversa += 1
        if contador == 9:
            return 'resultado ' + self.id_convite_enviado + ' empate empate', 'empate'
        contador = 0
        casas_marcadas_D = 0
        casas_marcadas_D_inversa = 0
        for i in range(3):
            casas_marcadas_V = 0
            casas_marcadas_H = 0
            for j in range(3):
                if self.tabuleiro[i][j] != CASA_VAZIA:
                    contador += 1
                if self.tabuleiro[j][i] == CONVIDADO:
                    casas_marcadas_V += 1
                if self.tabuleiro[i][j] == CONVIDADO:
                    casas_marcadas_H += 1
            if casas_marcadas_H == 3 or casas_marcadas_V == 3:
                if self.minha_peca == CONVIDADO:
                    return 'resultado ' + self.id_convite_enviado + ' ' + self.usuario + ' ' + self.adversario_atual, 'vitoria'
                else:
                    return 'resultado ' + self.id_convite_enviado + ' ' + self.adversario_atual + ' ' + self.usuario, 'derrota'
            if self.tabuleiro[i][i] == CONVIDADO:
                casas_marcadas_D += 1
            if self.tabuleiro[i][2-i] == CONVIDADO:
                casas_marcadas_D_inversa += 1

        return False, False

    def termina_partida(self):
        self.socket_p2p.close()
        self.id_convite_enviado = '0'
        self.tabuleiro = [[CASA_VAZIA for x in range(3)] for y in range(3)]
        self.minha_peca = None 
        self.em_jogo = False
        self.meu_turno = False
        self.adversario_atual = None
        self.status_jogo_atual = None
        self.socket_p2p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def main():
    HOST = sys.argv[1]  # The server's hostname or IP address
    PORT = int(sys.argv[2])
    PORT_SSL = int(sys.argv[3])
    PORT_P2P = int(sys.argv[4])
    cliente = Cliente(HOST, PORT, PORT_SSL, PORT_P2P)
    cliente.run()    
            
            


if __name__ == '__main__':
    main()
