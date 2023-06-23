import socket
import os
import json
import threading as th
 
class Peer:

    def __init__(self):
        self.ip = input()
        # self.ip = '127.0.1.' + input()
        self.port = int(input())
        # self.port = 2220 + int(input())
        self.path_folder = input()
        # self.path_folder = rf'PEERS_FOLDERS\PEER{input()}'

        if os.path.exists(self.path_folder):
            self.files = os.listdir(self.path_folder)
        else:
            os.mkdir(self.path_folder)
            self.files = []

        self.file_to_search = ''
        self.join_request_done = False

        self.peer = socket.socket()
        self.peer.connect(('127.0.0.1', 1099))

        self.set_request()

        self.peer.close()

    def set_request(self):
        while True:
            try:
                print('O QUE DESEJA FAZER? [JOIN, SEARCH, DOWNLOAD]')
                request = input()
                
                self.peer.send(json.dumps(request).encode())

                if request == 'JOIN' and not self.join_request_done:
                    self.join_request()
                    self.join_request_done = True       

                    # cria thread para o peer aceitar solicitação de download
                    download_thread = th.Thread(target=self.download_recv_request)
                    download_thread.start()                            

                elif request == 'SEARCH':
                    self.peers_with_file = self.search_request()

                elif request == 'DOWNLOAD':
                    self.download_send_request()

                    self.peer.send(json.dumps('UPDATE').encode())

                    self.update_request()     

            except KeyboardInterrupt:
                break

    def join_request(self):
        # cria variavel com as informações do peer
        peer_files = {'files': self.files}

        # envia uma requisição de join pro servidor com todas suas informações (lista de nomes de arquivos)
        self.peer.send(json.dumps(peer_files).encode())
        
        # deve esperar o 'JOIN_OK'
        if json.loads(self.peer.recv(1024).decode()) == 'JOIN_OK':
            print(f"Sou peer {self.ip}:{self.port} com arquivos {' '.join(self.files)}")
            return
    
    def search_request(self):
        # envia uma requisição de search pro servidor com o nome do arquivo que deseja baixar
        self.file_to_search = input()

        self.peer.send(json.dumps(self.file_to_search).encode())

        peers_with_file = json.loads(self.peer.recv(1024).decode())
        peers_with_file = [ip + ':' + str(port) for ip, port in peers_with_file]

        # recebera uma lista
        print(f"Peers com arquivo solicitado: {' '.join(peers_with_file)}")

        return peers_with_file
    
    def update_request(self):
        # APÓS O ARQUIVO SER BAIXADO
        # envia uma requisição de update pro servidor com o nome do arquivo que deseja adicionar a sua lista
        file_to_update = input()

        self.peer.send(json.dumps(file_to_update).encode())

        # deve esperar o 'UPDATE_OK'
        if json.loads(self.peer.recv(1024).decode()) == 'UPDATE_OK':
            return
    
    def download_send_request(self):
        ip_download = input()
        port_download = int(input())

        self.peer.connect((ip_download, port_download))
        self.peer.send(json.dumps(self.file_to_search).encode())
        print(f'CONNECTOU E SOLICITOU O ARQUIVO PARA {(ip_download, port_download)}')
        
        with open(self.path_folder + '\\' + self.file_to_search, 'wb') as new_file:
            while True:
                data = self.peer.recv(1024).decode()

                if data:
                    new_file.write(json.loads(data))
                else: 
                    break

        print(f"Arquivo {self.file_to_search} baixado com sucesso na pasta {self.path_folder}")

        return
    
    def download_recv_request(self):
        self.peer_server = socket.socket()

        self.peer_server.bind((self.ip, self.port))

        self.peer_server.listen()

        print(f'SOCKET PEER_SERVER: {self.peer_server.getsockname()}')

        while True:
            try:
                peer, peer_addr = self.peer_server.accept()

                file_to_search = json.loads(peer.recv(1024).decode())

                path_file = self.path_folder + '\\' + file_to_search

                if os.path.exists(path_file):
                    with open(path_file, 'r') as file:
                        while True:
                            data = file.read(1024)

                            if data:
                                peer.send(json.dumps(data).encode())

                            else:
                                print(f'ENVIADO ARQUIVO {file_to_search}')
                                break 

            except KeyboardInterrupt:
                break


Peer()   