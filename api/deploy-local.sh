#!/bin/bash

# Script de Deploy Local para API Cripto Prediction
set -e

echo "🚀 Iniciando deploy local da API Cripto Prediction..."

# Configurações
PYTHON_VERSION="3.9"
PORT="8000"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log colorido
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# 1. Verificar se Python está instalado
log "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    error "Python 3 não está instalado."
fi

PYTHON_VERSION_CHECK=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
log "Python versão: $PYTHON_VERSION_CHECK"

# 2. Verificar se pip está instalado
log "Verificando pip..."
if ! command -v pip3 &> /dev/null; then
    error "pip3 não está instalado."
fi

# 3. Criar ambiente virtual se não existir
log "Configurando ambiente virtual..."
if [ ! -d "venv" ]; then
    log "Criando ambiente virtual..."
    python3 -m venv venv
fi

# 4. Ativar ambiente virtual
log "Ativando ambiente virtual..."
source venv/bin/activate

# 5. Instalar dependências
log "Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Verificar se AWS CLI está configurado
log "Verificando configuração AWS..."
if ! aws sts get-caller-identity &> /dev/null; then
    warning "AWS CLI não está configurado. A API pode não conseguir acessar o S3."
    warning "Execute 'aws configure' para configurar as credenciais."
fi

# 7. Verificar se o bucket S3 existe
log "Verificando bucket S3..."
if aws s3 ls s3://criptos-data &> /dev/null; then
    log "✅ Bucket S3 encontrado: criptos-data"
else
    warning "⚠️ Bucket S3 'criptos-data' não encontrado ou não acessível."
    warning "Certifique-se de que o bucket existe e você tem permissões de acesso."
fi

# 8. Verificar se há modelos no S3
log "Verificando modelos no S3..."
MODEL_COUNT=$(aws s3 ls s3://criptos-data/models/ --recursive | grep -c ".joblib" || echo "0")
log "Encontrados $MODEL_COUNT arquivos de modelo no S3"

if [ "$MODEL_COUNT" -eq "0" ]; then
    warning "⚠️ Nenhum modelo encontrado no S3."
    warning "Execute o treinamento de modelos primeiro."
fi

# 9. Iniciar a API
log "Iniciando API..."
log "🌐 API será disponibilizada em: http://localhost:$PORT"
log "📚 Documentação: http://localhost:$PORT/docs"
log "🔍 Health Check: http://localhost:$PORT/health"
log ""

# 10. Executar a API
log "Executando uvicorn..."
echo "Pressione Ctrl+C para parar a API"
echo ""

cd app
python -m uvicorn main:app --host 0.0.0.0 --port $PORT --reload 