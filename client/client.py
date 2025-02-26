import os
import random
import time
import requests
from flask import Flask, request, jsonify
import logging

# Desabilitar logs do urllib3
logging.getLogger('urllib3').setLevel(logging.WARNING)


app = Flask(__name__)

# ID do cliente, passado como variável de ambiente
client_id = int(os.getenv('CLIENT_ID', 1))

# URL do nó ao qual este cliente está vinculado
base_url = f'http://node{client_id}:5000'

@app.route('/receive_committed', methods=['POST'])
def receive_committed():
    """Recebe a mensagem COMMITTED e entra em espera antes de continuar."""
    print(f"Cliente {client_id} recebeu COMMITTED e está aguardando.")
    sleep_time = random.uniform(1, 5)
    time.sleep(sleep_time)  # Simula tempo de processamento
    return jsonify({"status": "Wait complete"})

def request_access():
    """Solicita acesso ao recurso do nó associado a este cliente."""
    url = f'{base_url}/request_access'
    try:
        response = requests.post(url, json={'client_id': client_id})
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao solicitar acesso ao nó: {e}")
        return {"status": "Erro ao conectar ao nó"}

if __name__ == '__main__':
    for _ in range(random.randint(10, 50)):  # Solicita entre 10 e 50 acessos
        print(f"Cliente {client_id} solicitando acesso ao recurso.")
        response = request_access()
        if response.get('status') == 'Requisição adicionada à fila e será processada':
            print(f"Cliente {client_id} recebeu confirmação e está aguardando.")
        else:
            print(f"Cliente {client_id} não recebeu confirmação.")
