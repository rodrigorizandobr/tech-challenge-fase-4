#!/bin/bash

# Script de Deploy para Lambda + API Gateway
set -e

echo "🚀 Iniciando deploy da API Lambda Cripto Prediction..."

# Configurações
AWS_REGION="us-east-1"
LAMBDA_FUNCTION_NAME="cripto-prediction-api"

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

# 1. Verificar se AWS CLI está configurado
log "Verificando configuração AWS..."
if ! aws sts get-caller-identity &> /dev/null; then
    error "AWS CLI não está configurado. Execute 'aws configure' primeiro."
fi

# 2. Verificar se Python está instalado
log "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    error "Python3 não está instalado."
fi

# 3. Criar diretório temporário
log "Criando diretório temporário..."
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

# 4. Copiar arquivos necessários
log "Copiando arquivos..."
cp $OLDPWD/lambda_function.py .
cp $OLDPWD/requirements-lambda.txt requirements.txt

# 5. Instalar dependências
log "Instalando dependências..."
pip3 install -r requirements.txt -t .

# 6. Criar ZIP do Lambda
log "Criando ZIP do Lambda..."
zip -r lambda_function.zip . -x "*.pyc" "__pycache__/*" "*.git*"

# 7. Mover ZIP para diretório do projeto
log "Movendo arquivo ZIP..."
mv lambda_function.zip $OLDPWD/terraform-lambda/

# 8. Limpar diretório temporário
cd ../..
rm -rf $TEMP_DIR

# 9. Inicializar Terraform
log "Inicializando Terraform..."
cd $OLDPWD/terraform-lambda
terraform init

# 10. Aplicar infraestrutura
log "Aplicando infraestrutura..."
terraform apply -auto-approve

# 11. Obter URL da API
log "Obtendo URL da API..."
API_URL=$(terraform output -raw api_gateway_url)

if [ -z "$API_URL" ]; then
    warning "URL da API não encontrada. Verifique os outputs do Terraform."
else
    log "✅ Deploy concluído com sucesso!"
    echo ""
    echo "🌐 URL da API: $API_URL"
    echo "📊 Health Check: $API_URL/health"
    echo "📚 Documentação: $API_URL/docs"
    echo "🔍 Predição exemplo: $API_URL/symbol/BTC"
    echo ""
    echo "📋 Comandos úteis:"
    echo "  aws logs tail /aws/lambda/$LAMBDA_FUNCTION_NAME --follow"
    echo "  terraform output"
    echo "  aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME response.json"
fi

log "Deploy concluído! 🎉" 