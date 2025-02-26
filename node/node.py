import os
import random
import time
import threading
import requests
from flask import Flask, request, jsonify
import logging

# Desabilitar logs do urllib3
logging.getLogger('urllib3').setLevel(logging.WARNING)


app = Flask(__name__)

# ID do nó atual, passado como variável de ambiente
node_id = int(os.getenv('NODE_ID', 1))

# Lista de todos os nós no cluster, exceto este nó
nodes = [f'http://node{i}:5000' for i in range(1, 6) if i != node_id]

# Variáveis de controle
random_number = 999999999
ok_received = []
in_critical_section = False
request_queue = []
processing_request = False
nodes_in_critical_section = set()  # Conjunto para acompanhar quais nós já acessaram a seção crítica

def send_number_to_others():
    """Envia o número aleatório para os outros nós para negociação de acesso."""
    global random_number
    random_number = random.randint(1, 1000)
    print(f"Nó {node_id} gerou número {random_number} e quer entrar na área crítica.")
    
    # Enviar número para todos os outros nós
    for node in nodes:
        url = f'{node}/receive_number'
        try:
            requests.post(url, json={'node_id': node_id, 'random_number': random_number})
        except requests.exceptions.RequestException as e:
            print(f"Falha ao enviar número para {node}: {e}")

def enter_critical_section():
    """Entra na seção crítica quando todos os OKs foram recebidos."""
    global in_critical_section, processing_request
    if len(ok_received) == len(nodes):
        in_critical_section = True
        processing_request = True
        nodes_in_critical_section.add(node_id)  # Registra que o nó acessou a seção crítica
        print(f"Nó {node_id} entrou na área crítica!")
        time.sleep(random.uniform(0.2, 1.0))  # Simula uso do recurso
        exit_critical_section()

def exit_critical_section():
    """Sai da seção crítica e verifica se todos os nós acessaram a área crítica."""
    global in_critical_section, ok_received, processing_request
    in_critical_section = False
    ok_received = []
    processing_request = False
    print(f"Nó {node_id} saiu da área crítica.")

    # Notifica outros nós que saiu da seção crítica
    for node in nodes:
        url = f'{node}/ok'
        try:
            requests.post(url, json={'node_id': node_id})
        except requests.exceptions.RequestException as e:
            print(f"Falha ao enviar OK para {node}: {e}")

    # Verifica se todos os nós já acessaram a seção crítica antes de processar a próxima requisição
    if len(nodes_in_critical_section) == len(nodes) + 1:  # Inclui este nó na contagem
        print(f"Todos os nós completaram a rodada. Liberando próxima rodada de requisições.")
        nodes_in_critical_section.clear()  # Limpa para a próxima rodada

    process_next_request()  # Processa próxima requisição na fila

def process_next_request():
    """Processa a próxima requisição na fila, se disponível."""
    global processing_request
    if request_queue and not processing_request and len(nodes_in_critical_section) == 0:
        next_request = request_queue.pop(0)  # Retira a próxima requisição da fila
        print(f"Nó {node_id} processando próxima requisição da fila: {next_request}")
        send_number_to_others()

@app.route('/receive_number', methods=['POST'])
def receive_number():
    """Recebe um número aleatório de outro nó."""
    data = request.get_json()
    other_node_id = data['node_id']
    other_random_number = data['random_number']

    print(f"Nó {node_id} recebeu número {other_random_number} do nó {other_node_id}.")

    # Se o número recebido for menor que o do nó atual, envia confirmação (OK)
    if other_random_number < random_number:
        url = f'http://node{other_node_id}:5000/ok'
        try:
            requests.post(url, json={'node_id': node_id})
            ok_received.append(other_node_id)  # Adiciona apenas após enviar OK com sucesso
        except requests.exceptions.RequestException as e:
            print(f"Falha ao enviar OK para {other_node_id}: {e}")

    enter_critical_section()  # Tenta entrar na seção crítica se OKs suficientes forem recebidos
    return jsonify({"status": "Number received"})

@app.route('/ok', methods=['POST'])
def receive_ok():
    """Recebe uma confirmação (OK) de outro nó."""
    data = request.get_json()
    other_node_id = data['node_id']

    print(f"Nó {node_id} recebeu OK do nó {other_node_id}.")
    ok_received.append(other_node_id)
    enter_critical_section()
    return jsonify({"status": "OK received"})

@app.route('/request_access', methods=['POST'])
def request_access():
    """Recebe requisição de um cliente para acessar o recurso."""
    global request_queue, processing_request
    client_data = request.get_json()
    print(f"Nó {node_id} recebeu solicitação de cliente: {client_data}")

    # Adiciona requisição à fila
    request_queue.append(client_data)
    print(f"Requisição adicionada à fila no nó {node_id}. Fila atual: {request_queue}")

    # Se não estiver processando outra requisição, inicia o processamento da fila
    if not processing_request:
        process_next_request()

    return jsonify({"status": "Requisição adicionada à fila e será processada"})

@app.route('/committed', methods=['POST'])
def committed():
    """Notifica o cliente que o acesso foi concedido."""
    data = request.get_json()
    client_id = data.get('client_id')

    if not client_id:
        return jsonify({"error": "Cliente não especificado"}), 400

    url = f'http://client{client_id}:5000/receive_committed'
    try:
        requests.post(url, json={'node_id': node_id})
        print(f"COMMITTED enviado para cliente {client_id}.")
    except requests.exceptions.RequestException as e:
        print(f"Falha ao enviar COMMITTED para cliente {client_id}: {e}")

    return jsonify({"status": "COMMITTED sent"})

if __name__ == '__main__':
    # O Gunicorn será responsável por iniciar o servidor. Não é necessário app.run() aqui.
    pass
