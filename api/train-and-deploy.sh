#!/bin/bash

# Script para treinar modelos e fazer deploy da API
set -e

echo "🚀 Treinando modelos e fazendo deploy da API..."

# Configurações
AWS_REGION="us-east-1"
BUCKET_NAME="criptos-data"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# 1. Verificar se AWS CLI está configurado
log "Verificando configuração AWS..."
if ! aws sts get-caller-identity &> /dev/null; then
    error "AWS CLI não está configurado. Execute 'aws configure' primeiro."
fi

# 2. Verificar se o bucket existe
log "Verificando bucket S3..."
if ! aws s3 ls s3://$BUCKET_NAME &> /dev/null; then
    error "Bucket S3 '$BUCKET_NAME' não encontrado. Crie o bucket primeiro."
fi

# 3. Treinar modelos
log "Iniciando treinamento de modelos..."
cd ../models

# Verificar se Terraform está instalado
if ! command -v terraform &> /dev/null; then
    error "Terraform não está instalado."
fi

# Inicializar Terraform se necessário
if [ ! -d ".terraform" ]; then
    log "Inicializando Terraform..."
    terraform init
fi

# Aplicar infraestrutura
log "Aplicando infraestrutura com Terraform..."
terraform apply -auto-approve

# Aguardar treinamento
log "Aguardando treinamento dos modelos..."
sleep 60

# 4. Verificar se os modelos foram criados
log "Verificando modelos treinados..."
MODEL_COUNT=0
MAX_ATTEMPTS=10
ATTEMPT=0

while [ $MODEL_COUNT -eq 0 ] && [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    log "Tentativa $ATTEMPT/$MAX_ATTEMPTS - Verificando modelos..."
    
    MODEL_COUNT=$(aws s3 ls s3://$BUCKET_NAME/models/ --recursive 2>/dev/null | grep -c ".joblib" || echo "0")
    
    if [ $MODEL_COUNT -eq 0 ]; then
        warning "Nenhum modelo encontrado ainda. Aguardando..."
        sleep 30
    fi
done

if [ $MODEL_COUNT -eq 0 ]; then
    error "Modelos não foram criados após $MAX_ATTEMPTS tentativas."
else
    info "✅ $MODEL_COUNT modelos encontrados!"
fi

# 5. Voltar para a pasta da API
cd ../api

# 6. Verificar modelos
log "Verificando estrutura dos modelos..."
./check-models.sh

# 7. Deploy da API
log "Iniciando deploy da API..."
./deploy-local.sh

# 8. Aguardar API inicializar
log "Aguardando API inicializar..."
sleep 10

# 9. Testar API
log "Testando API..."
if command -v python3 &> /dev/null; then
    # Instalar requests se necessário
    pip3 install requests 2>/dev/null || true
    
    # Testar API
    python3 test_api.py http://localhost:8000
else
    warning "Python3 não encontrado. Teste manualmente:"
    echo "curl http://localhost:8000/health"
    echo "curl http://localhost:8000/symbol/BTC"
fi

log "🎉 Processo concluído!"
echo ""
echo "📋 Resumo:"
echo "   ✅ Modelos treinados e salvos no S3"
echo "   ✅ API deployada e funcionando"
echo "   ✅ Testes executados"
echo ""
echo "🌐 API disponível em: http://localhost:8000"
echo "📚 Documentação: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health" 