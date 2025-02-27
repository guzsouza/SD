import os
import random
import time
import threading
import requests
from flask import Flask, request, jsonify
import logging
import os

# Desabilitar logs do urllib3
logging.getLogger('urllib3').setLevel(logging.WARNING)


app = Flask(__name__)

# ID do nó atual, passado como variável de ambiente
node_id = int(os.getenv('NODE_ID', 1))

# Lista de todos os nós no cluster, exceto este nó
nodes = [f'http://node{i}:5000' for i in range(1, 6) if i != node_id]




# Variáveis de controle
timestamp = 999999999
number_of_ok = 0
critical_zone_target = False
request_queue = []
name_arq = f'estado{node_id}.bin'



#Iniciliza o estado da variável de controle como 0
def initial_state():
    with open(f'{name_arq}', 'wb') as file:
        file.write(b'\x00') 
    
    print(f"Estado inicial do nó {node_id} foi inicializado como 0", flush=True)

# def critical_zone_read():
#     global node_id, name_arq

#     if os.path.exists(f'{name_arq}'):
#         with open(f'{name_arq}', 'r') as file:
#             estado = file.read().strip()
#             return estado == 'False'  # Retorna True ou False baseado no arquivo
#     else:
#         return False  # Se o arquivo não existe, considera False como estado inicial

def verify_next_request(request_id):
    global number_of_ok 
    global timestamp
    global node_id
    global request_queue
    global nodes
    
    create_new_timestamp()

    if not critical_section_active_status():
        
        
        valid_queue_nodes = are_request_queues_not_empty()
        
        print(f"Finalizando verificação de filas de requisições, número de nós com filas não vazias {len(valid_queue_nodes)}", flush=True)
        
        if not valid_queue_nodes: 
            if request_queue:
                print(f"Fila do nó {node_id} possui requisições, fila atual: {request_queue}", flush=True)  
                if not critical_section_active_status():
                    print(f"Alerta>>> Nó {node_id} prestes a entrar na zona crítica! Variável de controle {critical_zone_target}", flush=True)  
                    enter_critical_section(request_id)
                else:
                    print("Zona crítica ocupada", flush=True)
                    time.sleep(0.2)
                    verify_next_request(request_id)
            else:
                print("Nenhuma requisição em fila.", flush=True)
        else:    
            print("Fila não vazia encontrada.", flush=True)
            number_of_ok = len(nodes) - len(valid_queue_nodes)
            print("Verificando o próximo nó. (com 5 ok's)", flush=True)
        
            for current_node in valid_queue_nodes:
                url = f'{current_node}/compare_timestamps/{timestamp}/{node_id}'
                try:
                    response = requests.get(url, json={'timestamp': timestamp, 'node_id': node_id})
                    if response.status_code == 200:
                        if response.json():
                            number_of_ok += 1
                            print(f"O nó {current_node} tem o número menor que o nó {node_id}, logo o ok foi contabilizado, número de ok's: {number_of_ok}", flush=True)
                    else:
                        print(f"Falha ao acessar a fila do nó {current_node}.")
                        return False
                except requests.exceptions.RequestException as e:
                    print(f"Falha ao obter dados de {current_node}: {e}", flush=True)
                    return False
                
            if number_of_ok == 5:
                print("Todos os ok's foram recebidos, entrando na área crítica!", flush=True)
                if not critical_section_active_status():
                    print("Nenhum nó está na área crítica", flush=True)
                    enter_critical_section(request_id)
                else:
                    print("Zona crítica ocupada", flush=True)
                    time.sleep(0.2)
                    verify_next_request(request_id)
                    
                    
                
# @app.route('/ok/<int:other_id>', methods=['PATCH'])
# def ok(other_id):
#     """Recebe OK de outro nó."""
#     global number_of_ok, node_id
#     number_of_ok += 1
#     print(f"O nó {other_id} enviou um ok para o nó {node_id}. Número de OKs: {number_of_ok}", flush=True)

@app.route('/get_request_queue', methods=['GET'])
def get_request_queue():
    """Retorna a fila de requisições do nó especificado.""" 
    global request_queue
    
    try:
        return jsonify({'request_queue': request_queue}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": "Erro inesperado: " + str(e)}), 500

def are_request_queues_not_empty():
    global nodes
    
    
    """Verifica se as filas de requisições de todos os nós estão vazias."""
    nodes_not_empty = []
    
    for node in nodes:
        url = f'{node}/get_request_queue'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print(f"Fila de requisições do nó {node}: {data['request_queue']}")
                if data['request_queue']:
                    print(f"A fila de requisições do nó {node} não está vazia.")
                    nodes_not_empty.append(node)
            else:
                print(f"Falha ao acessar e verificar internamente a fila do nó {node}.")
        except requests.exceptions.RequestException as e:
            print(f"Falha ao obter dados de {node}: {e}", flush=True)
    
    
    return nodes_not_empty


@app.route('/get_data', methods=['GET'])
def get_node_data():
    
    global node_id, number_of_ok, critical_zone_target, request_queue
    
    """Retorna os dados do nó especificado.""" 
    try:
        return jsonify({
            'node_id': node_id,
            'number_of_ok': number_of_ok,
            'critical_zone_target': critical_zone_target,
            'request_queue': request_queue,
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": "Erro inesperado: " + str(e)}), 500


@app.route('/patch_list_of_zone/<int:other_id>/<int:enter_or_leave>', methods=['PATCH'])
def patch_list_of_zone(other_id, enter_or_leave):
    global critical_zone_target
    """Atualiza a lista de controle de alertas de zona crítica."""
    try:
        if enter_or_leave == 1:
            critical_zone_target = True
        elif enter_or_leave == 0:
            critical_zone_target = False
        return jsonify({
            'critical_zone_target': critical_zone_target,
        }), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": "Erro inesperado: " + str(e)}), 500
    

def critical_section_active_status():
    """Verifica se algum nó está na seção crítica, com rechecagem."""
    global critical_zone_target
    
    if critical_zone_target:
        return True
    
    time.sleep(0.2) 
    
    if critical_zone_target:
        return True
    
    return False


def create_new_timestamp():
    """Envia o número aleatório para os outros nós para negociação de acesso."""
    global timestamp
    global node_id
    
    timestamp = random.randint(1, 1000)
    print(f"Nó {node_id} gerou número {timestamp} e quer entrar na área crítica.", flush=True)
    
            
@app.route('/compare_timestamps/<int:other_timestamp>/<int:other_id>', methods=['GET'])
def compare_timestamps(other_timestamp, other_id):
    """Compara o timestamp deste nó com o timestamp de outro nó."""
    global node_id, timestamp
    
    if timestamp > other_timestamp:
        print(f"O nó {node_id} tem o numero : {timestamp} já o nó {other_id} tem o número: {other_timestamp}, logo o timestamp do nó {other_id} é menor", flush=True)
        return True
    return False

def enter_critical_section(request_id):
    """Entra na seção crítica quando todos os OKs foram recebidos."""
    global critical_zone_target
    global request_queue
    
    
    # Atualiza a lista de alertas de zona crítica, inserindo o nó na zona
    if not critical_section_active_status():
        critical_zone_target = True
        for current_node in nodes:
            
            url = f'{current_node}/patch_list_of_zone/{node_id}/1'
            try:
                requests.patch(url, json={'node_id': node_id, 'enter_or_leave': 1})
            except requests.exceptions.RequestException as e:
                print(f"Falha ao enviar alerta para {current_node}: {e}", flush=True)
        
    
    print(f"Nó {node_id} está na zona crítica! Variável de controle {critical_zone_target}", flush=True)
    print(f"Nó {node_id} está executando a requisição do cliente {request_queue[0]}", flush=True)
    time.sleep(random.uniform(0.2, 1.0))  # Simula uso do recurso
    request_queue.pop(0)
    
    exit_critical_section(request_id)

def exit_critical_section(request_id):
    """Sai da seção crítica e verifica se todos os nós acessaram a área crítica."""
    global critical_zone_target, number_of_ok, request_queue

    
    #client_id = request_id  # Obtém o ID do cliente

    # if client_id:
    #     client_url = f'http://client{client_id}:5000/receive_committed'
    #     try:
    #         requests.post(client_url)
    #         print(f"Notificado o cliente {client_id} sobre o COMMITTED.", flush=True)
    #     except requests.exceptions.RequestException as e:
    #         print(f"Falha ao notificar o cliente {client_id}: {e}", flush=True)
    # else:
    #     print("Nenhum cliente encontrado para notificar sobre o COMMITTED.", flush=True)

    # Atualiza a lista de alertas de zona crítica, retirando o nó da zona
    critical_zone_target = False
    for current_node in nodes:
        url = f'{current_node}/patch_list_of_zone/{node_id}/0'
        try:
            requests.patch(url, json={'node_id': node_id, 'enter_or_leave': 0})
        except requests.exceptions.RequestException as e:
            print(f"Falha ao enviar alerta para {current_node}: {e}", flush=True)
            
    number_of_ok = 0

    print(f"Nó {node_id} saiu da área crítica.", flush=True)

    # # Notifica outros nós que saiu da seção crítica
    # for node in nodes:
    #     url = f'{node}/ok/{node_id}'
    #     try:
    #         requests.patch(url, json={'node_id': node_id})
    #     except requests.exceptions.RequestException as e:
    #         print(f"Falha ao enviar OK para {node}: {e}", flush=True)
            

@app.route('/request_access', methods=['POST'])
def request_access():
    """Recebe requisição de um cliente para acessar o recurso."""
    global request_queue
    global node_id
    
    initial_state()
    
    client_data = request.get_json()
    client_id = client_data.get('client_id')
    print(f"Nó {node_id} recebeu solicitação do cliente: {client_id}", flush=True)

    # Adiciona requisição à fila
    request_queue.append(client_id)
    print(f"Requisição adicionada à fila no nó {node_id}. Fila atual: {request_queue}", flush=True)
    
    verify_next_request(client_id)
    
    return jsonify({"status": "Requisição adicionada à fila e será processada quando possível"})


if __name__ == '__main__':
    # O Gunicorn será responsável por iniciar o servidor. Não é necessário app.run() aqui.
    pass
