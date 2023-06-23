import socket
import os
import json
import threading as th

class Server:

    def __init__(self):
        # self.ip = input() # 127.0.0.1
        self.ip = '127.0.0.1'
        # self.port = int(input()) # 1099
        self.port = 1099

        self.peers_list = []

        self.server = socket.socket()

        self.server.bind(('', self.port)) 

        self.server.listen(5)

        while True:
            try:
                peer, peer_addr = self.server.accept()

                # criar thread de request de 1 peer
                th.Thread(target=self.get_request, args=(peer, peer_addr)).start()

            except KeyboardInterrupt:
                break    

    def get_request(self, peer, peer_addr):
        while True:
            try:     
                request = json.loads(peer.recv(1024).decode())   

                if request == 'JOIN':
                    self.join_request(peer, peer_addr)

                elif request == 'SEARCH':
                    self.search_request(peer, peer_addr)

                elif request == 'UPDATE':
                    self.update_request(peer, peer_addr)
                
            except KeyboardInterrupt:
                break
        

    def join_request(self, peer, peer_addr):
        # recebe todas as infos do peer (ip, porta, lista de nome de arquivos)
        peer_infos = json.loads(peer.recv(1024).decode())

        # adiciona um novo peer na lista
        self.peers_list.append({
            'addr':peer_infos['addr']
            ,'addr_conn': peer_addr
            ,'files':peer_infos['files']
            })
        
        peer.send(json.dumps('JOIN_OK').encode())

        print(f"Peer {self.peers_list[-1]['addr'][0]}:{self.peers_list[-1]['addr'][1]} adicionado com arquivos {' '.join(self.peers_list[-1]['files'])}")

        return
    
    def search_request(self, peer, peer_addr):
        # recebe do peer solicitante o nome do arquivo a ser procurado
        file_to_search = json.loads(peer.recv(1024).decode())

        # procura na lista pelo peer que solicitou o arquivo
        for peer_connected in self.peers_list:
            if peer_connected['addr_conn'] == peer_addr:
                peer_searching = peer_connected['addr']
        # arquivo solicitado
        print(f"Peer {peer_searching[0]}:{peer_searching[1]} solicitou arquivo {file_to_search}")
        
        # procura na lista de peer pelos que contenham o arquivo X
        peers_with_file = [peer_connected['addr'] for peer_connected in self.peers_list if file_to_search in peer_connected['files']]

        # retorna uma lista com todas as infos dos peers q tem o arquivo
        peer.send(json.dumps(peers_with_file).encode())

        return 

    def update_request(self, peer, peer_addr):
        # recebe do peer nome do arquivo a ser atualizado
        file_to_update = json.loads(peer.recv(1024).decode())

        # procura na lista pelo peer e adiciona o arquivo na sua lista
        for peer_connected in self.peers_list:
            if peer_connected['addr_conn'] == peer_addr and file_to_update not in peer_connected['files']:
                peer_connected['files'].append(file_to_update)

        # retorna 'UPDATE_OK'
        peer.send(json.dumps('UPDATE_OK').encode())

        print(f'LISTA ATUALIZADA: {self.peers_list}')

        return
    
Server()