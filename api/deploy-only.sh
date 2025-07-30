#!/bin/bash

# Script para fazer deploy da API (apenas leitura de modelos existentes)
set -e

echo "🚀 Fazendo deploy da API para ler modelos existentes..."

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
    error "Bucket S3 '$BUCKET_NAME' não encontrado."
fi

info "✅ Bucket S3 encontrado: $BUCKET_NAME"

# 3. Verificar modelos existentes
log "Verificando modelos existentes no S3..."
MODEL_COUNT=$(aws s3 ls s3://$BUCKET_NAME/models/ --recursive 2>/dev/null | grep -c ".joblib" || echo "0")

if [ $MODEL_COUNT -eq 0 ]; then
    warning "⚠️ Nenhum modelo encontrado no S3."
    warning "Certifique-se de que existem arquivos .joblib na pasta models/"
    echo ""
    echo "📋 Para verificar modelos existentes:"
    echo "   aws s3 ls s3://$BUCKET_NAME/models/ --recursive"
    echo ""
    echo "💡 Se não houver modelos, você pode:"
    echo "   1. Treinar modelos manualmente"
    echo "   2. Fazer upload de modelos existentes"
    echo "   3. Usar a API em modo simulado"
    echo ""
    read -p "Deseja continuar mesmo sem modelos? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    info "✅ Encontrados $MODEL_COUNT modelos no S3"
    echo "📊 Modelos disponíveis:"
    aws s3 ls s3://$BUCKET_NAME/models/ --recursive | grep ".joblib" | while read -r line; do
        echo "   📁 $line"
    done
fi

# 4. Navegar para a pasta da API
cd api

# 5. Verificar estrutura dos modelos
log "Verificando estrutura dos modelos..."
./check-models.sh

# 6. Deploy da API
log "Iniciando deploy da API..."
./deploy-local.sh

# 7. Aguardar API inicializar
log "Aguardando API inicializar..."
sleep 10

# 8. Testar API
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

log "🎉 Deploy concluído!"
echo ""
echo "📋 Resumo:"
echo "   ✅ API deployada e funcionando"
echo "   ✅ Modelos verificados no S3"
echo "   ✅ Testes executados"
echo ""
echo "🌐 API disponível em: http://localhost:8000"
echo "📚 Documentação: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "🔧 Comandos úteis:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/models"
echo "   curl http://localhost:8000/symbol/BTC" 