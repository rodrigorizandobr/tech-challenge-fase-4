#!/bin/bash

# Script de deploy do crawler da Binance
set -e

echo "🚀 Iniciando deploy do crawler da Binance..."

# Verificar se o AWS CLI está instalado
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI não encontrado. Por favor, instale o AWS CLI primeiro."
    exit 1
fi

# Verificar se o Terraform está instalado
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform não encontrado. Por favor, instale o Terraform primeiro."
    exit 1
fi

# Verificar se o Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado. Por favor, instale o Node.js primeiro."
    exit 1
fi

echo "📦 Instalando dependências do Lambda..."
cd lambda
npm install
echo "✅ Dependências instaladas"

echo "📦 Criando pacote do Lambda..."
npm run package
echo "✅ Pacote criado"

cd ..

echo "🏗️ Inicializando Terraform..."
cd terraform
terraform init

echo "📋 Verificando plano do Terraform..."
terraform plan

echo "❓ Deseja aplicar as mudanças? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "🚀 Aplicando configuração do Terraform..."
    terraform apply -auto-approve
    echo "✅ Deploy concluído com sucesso!"
    
    echo "📊 Informações do deploy:"
    echo "S3 Bucket: $(terraform output -raw s3_bucket_name)"
    echo "Lambda Function: $(terraform output -raw lambda_function_name)"
    echo "CloudWatch Logs: $(terraform output -raw cloudwatch_log_group)"
else
    echo "❌ Deploy cancelado pelo usuário"
    exit 1
fi

cd ..

echo "🎉 Deploy concluído! O crawler será executado automaticamente a cada hora."
echo "📝 Para verificar os logs: aws logs tail /aws/lambda/binance-crawler --follow" 