# Usando a imagem oficial do Python
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar os arquivos para o diretório de trabalho dentro do container
COPY requirements.txt /app/requirements.txt
COPY client.py /app/client.py

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta para a aplicação
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "node:app"]

