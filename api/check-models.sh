#!/bin/bash

# Script para verificar modelos no S3
set -e

echo "🔍 Verificando modelos no S3..."

# Configurações
BUCKET_NAME="criptos-data"
AWS_REGION="us-east-1"

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
    error "Bucket S3 '$BUCKET_NAME' não encontrado ou não acessível."
fi

info "✅ Bucket S3 encontrado: $BUCKET_NAME"

# 3. Listar todos os arquivos no bucket
log "Listando arquivos no bucket..."
aws s3 ls s3://$BUCKET_NAME --recursive --human-readable

# 4. Verificar especificamente a pasta models
log "Verificando pasta models..."
MODEL_FILES=$(aws s3 ls s3://$BUCKET_NAME/models/ --recursive 2>/dev/null | grep ".joblib" || echo "")

if [ -z "$MODEL_FILES" ]; then
    warning "⚠️ Nenhum arquivo .joblib encontrado na pasta models/"
else
    info "📊 Arquivos de modelo encontrados:"
    echo "$MODEL_FILES" | while read -r line; do
        if [[ $line == *".joblib"* ]]; then
            echo "   📁 $line"
        fi
    done
fi

# 5. Verificar estrutura de dados
log "Verificando dados de exemplo..."
DATA_FILES=$(aws s3 ls s3://$BUCKET_NAME/data/ --recursive 2>/dev/null | head -10 || echo "")

if [ -z "$DATA_FILES" ]; then
    warning "⚠️ Nenhum arquivo de dados encontrado na pasta data/"
else
    info "📊 Arquivos de dados encontrados (primeiros 10):"
    echo "$DATA_FILES" | while read -r line; do
        echo "   📄 $line"
    done
fi

# 6. Verificar arquivo de controle
log "Verificando arquivo de controle..."
CONTROL_FILE=$(aws s3 ls s3://$BUCKET_NAME/models/latest_models.txt 2>/dev/null || echo "")

if [ -z "$CONTROL_FILE" ]; then
    warning "⚠️ Arquivo de controle 'models/latest_models.txt' não encontrado"
else
    info "✅ Arquivo de controle encontrado"
    echo "📋 Conteúdo do arquivo de controle:"
    aws s3 cp s3://$BUCKET_NAME/models/latest_models.txt - 2>/dev/null || echo "   (vazio ou não acessível)"
fi

# 7. Verificar permissões
log "Verificando permissões..."
BUCKET_ACL=$(aws s3api get-bucket-acl --bucket $BUCKET_NAME 2>/dev/null || echo "Não acessível")

if [[ $BUCKET_ACL == *"FULL_CONTROL"* ]]; then
    info "✅ Permissões completas no bucket"
elif [[ $BUCKET_ACL == *"READ"* ]]; then
    info "✅ Permissões de leitura no bucket"
else
    warning "⚠️ Permissões limitadas no bucket"
fi

# 8. Resumo
echo ""
echo "📋 RESUMO DA VERIFICAÇÃO"
echo "========================"
echo "Bucket: $BUCKET_NAME"
echo "Região: $AWS_REGION"

MODEL_COUNT=$(aws s3 ls s3://$BUCKET_NAME/models/ --recursive 2>/dev/null | grep -c ".joblib" || echo "0")
DATA_COUNT=$(aws s3 ls s3://$BUCKET_NAME/data/ --recursive 2>/dev/null | wc -l || echo "0")

echo "Modelos encontrados: $MODEL_COUNT"
echo "Arquivos de dados: $DATA_COUNT"

if [ "$MODEL_COUNT" -gt 0 ]; then
    echo "✅ Modelos disponíveis para a API"
else
    echo "❌ Nenhum modelo encontrado"
    echo ""
    echo "💡 Para treinar modelos, execute:"
    echo "   cd ../models"
    echo "   terraform apply"
fi

echo ""
echo "🔧 Para testar a API:"
echo "   cd api"
echo "   ./deploy-local.sh"
echo ""
echo "🧪 Para testar a API:"
echo "   python test_api.py http://localhost:8000" 