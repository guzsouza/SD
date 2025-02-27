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

base_url = f'http://node{client_id}:5000'


@app.route('/receive_committed', methods=['POST'])
def receive_committed():
    """Recebe a mensagem COMMITTED e entra em espera antes de continuar."""
    print(f"Cliente {client_id} recebeu COMMITTED e está aguardando.", flush=True)
    sleep_time = random.uniform(1, 5)
    time.sleep(sleep_time)  # Simula tempo de processamento
    return jsonify({"status": "Wait complete"})

def request_access():
    
    global client_id
    """Solicita acesso ao recurso a um nó aleatório"""

    
    print(f"Cliente {client_id} solicitando acesso ao nó {base_url}.", flush=True)
    
    url = f'{base_url}/request_access'
    try:
        response = requests.post(url, json={'client_id': client_id})
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao solicitar acesso ao nó: {e}", flush=True)
        return {"status": "Erro ao conectar ao nó"}

if __name__ == '__main__':
    
    """O Processamento começa avisando que o cliente foi iniciado e depois solicita acesso ao recurso."""
    print(f"Cliente {client_id} iniciado.", flush=True)
    
    
    for _ in range(random.randint(5, 10)):  # Solicita entre 10 e 50 acessos
        print(f"Cliente {client_id} solicitando acesso ao recurso.", flush=True)
        time.sleep(1.0)
        response = request_access()
