import socket
import os
import json
import threading as th

class Server:

    def __init__(self):
        # INICIALIZA O SERVIDOR COM IP E PORTA
        self.ip = input() # 127.0.0.1
        self.port = int(input()) # 1099

        self.connected_peers_list = []

        self.server = socket.socket()

        self.server.bind(('', self.port)) 

        self.server.listen(5)

        while True:
            try:
                # AGUARDA PEER SOLICITAR CONEXAO
                peer, peer_addr = self.server.accept()

                # CRIA UMA THREAD PARA O PEER Q SOLICITOU A CONEXAO
                # E ENVIA PARA O CONTROLE DE REQUESTS
                th.Thread(target=self.get_request, args=(peer, peer_addr)).start()

            except KeyboardInterrupt:
                # ENCERRA O SERVIDOR
                break    

    def get_request(self, peer, peer_addr):
        while True:
            try:
                # RECEBE O REQUEST DO PEER E FAZ O CHAMADO PARA A RESPECTIVA FUNCAO
                request = peer.recv(1024).decode()

                if request == 'JOIN':
                    self.join_request(peer, peer_addr)

                elif request == 'SEARCH':
                    self.search_request(peer, peer_addr)

                elif request == 'UPDATE':
                    self.update_request(peer, peer_addr)
                
            except KeyboardInterrupt:
                # ENCERRA A THREAD
                break
        

    def join_request(self, peer, peer_addr):
        # AGUARDA RECEBER TODAS AS INFOS DO PEER (IP E PORTA DO SOCKET DE CONEXAO, IP E PORTA DO SOCKET DE UPLOAD E LISTA DE SEUS ARQUIVOS)
        peer_infos = json.loads(peer.recv(1024).decode())

        # ADICIONA ESSE PEER NA LISTA
        self.connected_peers_list.append({
            'addr_conn': peer_addr
            ,'addr':peer_infos['addr']
            ,'files':peer_infos['files']
            })
        
        # RETORNA 'JOIN_OK'
        peer.send('JOIN_OK'.encode())

        print(f"Peer {self.connected_peers_list[-1]['addr'][0]}:{self.connected_peers_list[-1]['addr'][1]} adicionado com arquivos {' '.join(self.connected_peers_list[-1]['files'])}")

        return
    
    def search_request(self, peer, peer_addr):
        # AGUARDA QUAL O NOME DO ARQUIVO DESEJADO
        file_to_search = peer.recv(1024).decode()

        # PROCURA QUAL PEER SOLICITOU O ARQUIVO
        for connected_peer in self.connected_peers_list:
            if connected_peer['addr_conn'] == peer_addr:
                peer_searching = connected_peer['addr']

        # INFORMA QUAL ARQUIVO FOI SOLICITADO
        print(f"Peer {peer_searching[0]}:{peer_searching[1]} solicitou arquivo {file_to_search}")
        
        # PROCURA QUAIS PEERS POSSUEM ESSE ARQUIVO E CRIA UMA LISTA COM SEUS ENDEREÇOS DE UPLOAD
        peers_with_file = [connected_peer['addr'] # ARMAZENA O ENDEREÇO NA LISTA CASO...
                            for connected_peer in self.connected_peers_list # AO PERCORRER UM A UM A LISTA DE PEERS CONECTADOS 
                                if file_to_search in connected_peer['files']] # O ARQUIVO DESEJADO SE ENCONTRA NA LISTA DO MESMO 

        # RETORNA O ENDEREÇO DOS QUE POSSUEM O ARQUIVO
        peer.send(json.dumps(peers_with_file).encode())

        return 

    def update_request(self, peer, peer_addr):
        # AGUARDA PARA RECEBER O NOME DO ARQUIVO A SER ATUALIZADO
        file_to_update = peer.recv(1024).decode()

        # PROCURA PELO PEER QUE FEZ A SOLICITAÇÃO
        for connected_peer in self.connected_peers_list:
            # SE ENCONTRAR E ELE JA NAO POSSUIR O ARQUIVO
            if connected_peer['addr_conn'] == peer_addr and file_to_update not in connected_peer['files']:
                # ADICIONA O ARQUIVO NA LISTA
                connected_peer['files'].append(file_to_update)

        # RETORNA O 'UPDATE_OK'
        peer.send('UPDATE_OK'.encode())

        return
    
Server()