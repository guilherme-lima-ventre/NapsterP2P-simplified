import socket
import os
import json
import threading as th
 
class Peer:

    def __init__(self):
        # INICIALIZA O PEER COM IP, PORTA E PASTA COM OS ARQUIVOS
        self.ip = input()
        self.port = int(input())
        self.path_folder = input()

        # CHECA SE A PASTA EXISTE E CRIA LISTA DE ARQUIVOS
        if os.path.exists(self.path_folder):
            self.files = os.listdir(self.path_folder)
            self.files = [file for file in self.files if os.path.isfile(self.path_folder + '\\' + file)]
        # SE NÃO EXISTE, CRIA A PASTA E A DEFINE COMO VAZIA
        else:
            os.mkdir(self.path_folder)
            self.files = []

        # INICIALIZAÇÃO DE VÁRIAVEIS
        self.file_to_search = ''
        self.join_request_done = False
        self.search_request_done = False
        self.download_request_done = False

        # INICIALIZA O PEER E CONECTA AO SERVER
        self.peer = socket.socket()
        self.peer.connect(('127.0.0.1', 1080))

        # VAI ATÉ O MENU DE REQUESTS
        self.set_request()

        # CASO INTERROMPA O MENU, ENCERRA A CONEXÃO
        self.peer.close()

    def set_request(self):
        while True:
            try:
                print('O QUE DESEJA FAZER? [JOIN, SEARCH, DOWNLOAD]')
                request = input().upper()

                if request == 'JOIN':
                    if self.join_request_done:
                        print('JOIN JA REALIZADO')
                    else:
                        # ENVIA AO SERVIDOR O JOIN REQUEST 
                        self.peer.send(request.encode())

                        self.join_request()
                        self.join_request_done = True       

                        # CRIA THREAD PARA FAZER UPLOAD SE SOLICITADO
                        th.Thread(target=self.upload_request).start()                         

                elif request == 'SEARCH':
                    if not self.join_request_done:
                        print('JOIN NAO REALIZADO')
                    else:
                        # ENVIA AO SERVIDOR O SEARCH REQUEST 
                        self.peer.send(request.encode())

                        self.search_request()
                        self.search_request_done = True
                        self.download_request_done = False

                elif request == 'DOWNLOAD':
                    if not self.join_request_done:
                        print('JOIN NAO REALIZADO')
                    elif not self.search_request_done:
                        print('SEARCH NAO REALIZADO')
                    elif not self.search_request_done:
                        print('DOWNLOAD JA REALIZADO')
                    else:
                        self.download_request()
                        self.download_request_done = True

                        # SOLICITA O UPDATE
                        self.peer.send('UPDATE'.encode())

                        self.update_request()
                
                else:
                    print('REQUEST INVÁLIDO')

            except KeyboardInterrupt:
                # ENCERRA A EXECUCAO DO PEER
                break

    def join_request(self):
        # LISTA COM ADDRESS E OS ARQUIVOS DO PEER
        peer_infos = {
            'addr': (self.ip, self.port)
            ,'files': self.files
            }

        # ENVIA PARA O SERVIDOR ESSA LISTA
        self.peer.send(json.dumps(peer_infos).encode())
        
        # AGUARDA O 'JOIN_OK'
        if self.peer.recv(1024).decode() == 'JOIN_OK':
            print(f"Sou peer {self.ip}:{self.port} com arquivos {' '.join(self.files)}")
            return
    
    def search_request(self):
        # DEFINE O ARQUIVO A SER PESQUISADO NOS OUTROS PEERS
        self.file_to_search = input()

        # ENVIA PARA O SERVIDOR ESSE ARQUIVO
        self.peer.send(self.file_to_search.encode())

        # RECEBE LISTA DE PEERS COM OS ARQUIVOS
        peers_with_file = json.loads(self.peer.recv(1024).decode())
        peers_with_file = [ip + ':' + str(port) for ip, port in peers_with_file]
        print(f"Peers com arquivo solicitado: {' '.join(peers_with_file)}")

        return
    
    def update_request(self):
        # APÓS O ARQUIVO SER BAIXADO
        # ENVIA PARA O SERVIDOR O ARQUIVO A SER ATUALIZADO
        self.peer.send(self.file_to_search.encode())

        # AGUARDA O 'UPDATE_OK'
        if self.peer.recv(1024).decode() == 'UPDATE_OK':
            return
    
    def download_request(self,):
        # CRIA NOVO SOCKET PARA RECEBER CONEXAO
        peer_client = socket.socket()

        # RECEBE IP E PORTA DO PEER QUE CONTEM O ARQUIVO
        ip_download = input()
        port_download = int(input())

        try:
            # ESTABELECE CONEXAO
            peer_client.connect((ip_download, port_download))

            # ENVIA ARQUIVO DESEJADO
            peer_client.send(self.file_to_search.encode())

            # DEFINE CAMINHO ONDE O ARQUIVO SERA BAIXADO
            path_file = self.path_folder + '\\' + self.file_to_search
            
            # CRIA UM NOVO ARQUIVO VAZIO NO FOLDER DO PEER
            with open(path_file, 'wb') as new_file:
                while True:
                    # RECEBE DO OUTRO PEER O TAMANHO DO TRECHO DO ARQUIVO 
                    data_size = int(peer_client.recv(1024).decode())
                    # INDICA QUE RECEBEU A INFORMAÇÃO
                    peer_client.send('OK'.encode())

                    # ENQUANTO HOUVER CONTEUDO ARQUIVO QUE SERA ENVIADO
                    # RECEBE ESSE CONTEUDO E ESCREVE NO NOVO ARQUIVO EM BYTES
                    if data_size != 0:
                        data = peer_client.recv(data_size)
                        new_file.write(data)
                    else:
                        break            

            print(f"Arquivo {self.file_to_search} baixado com sucesso na pasta {self.path_folder}")

            # APOS RECEBER O ARQUIVO ENCERRA A CONEXAO
            peer_client.close()

            return
    
        except:
            print(f'CONEXAO COM PEER {ip_download + ":" + str(port_download)} NÃO PODE SER ESTABELECIDA, DIGITE NOVAMENTE IP E PORTA')
            peer_client.close()
            self.download_request()
    
    def upload_request(self):
        # INICIALIZA UM SOCKET PARA PODER ENVIAR ARQUIVOS SOLICITADOS
        peer_server = socket.socket()

        peer_server.bind((self.ip, self.port))

        peer_server.listen()

        while True:
            try:
                # AGUARDA E ACEITA SOLICITAÇÕES
                peer, peer_addr = peer_server.accept()

                # CRIA THREAD PARA FAZER MAIS DE 1 UPLOAD POR VEZ SE SOLICITADO
                th.Thread(target=self.upload, args=(peer,)).start() 

            except KeyboardInterrupt:
                # ENCERRA A THREAD
                break 

    def upload(self, peer):
        # RECEBE O ARQUIVO A SER BAIXADO
        file_to_search = peer.recv(1024).decode()

        path_file = self.path_folder + '\\' + file_to_search

        # CHECA SE REALMENTE POSSUI O ARQUIVO
        if os.path.exists(path_file):
            # ABRE SEU ARQUIVO, FAZENDO SUA LEITURA EM BYTES
            with open(path_file, 'rb') as file:
                while True:
                    data = file.read(1024)
                    # ENVIA O TAMANHO DO TRECHO QUE SERA ENVIADO
                    peer.send(str(len(data)).encode())

                    # SE O PEER RECEBEU O TAMANHO, ENVIA O CONTEUDO
                    if data and peer.recv(2048).decode() == 'OK':
                        peer.send(data)
                    else:
                        break

        return

Peer()   