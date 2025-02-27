# Usando a imagem oficial do Python
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar apenas os arquivos necessários para instalar dependências
COPY requirements.txt /app/requirements.txt

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante dos arquivos para o diretório de trabalho dentro do container
COPY . /app

# Expor a porta para a aplicação
EXPOSE 5000

# Comando para rodar a aplicação com Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "node:app"]
