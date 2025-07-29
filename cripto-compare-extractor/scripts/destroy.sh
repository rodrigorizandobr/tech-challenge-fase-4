#!/bin/bash

# Script para destruir a infraestrutura do crawler da Binance
set -e

echo "🗑️ Iniciando destruição da infraestrutura do crawler da Binance..."

# Verificar se o Terraform está instalado
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform não encontrado. Por favor, instale o Terraform primeiro."
    exit 1
fi

echo "⚠️ ATENÇÃO: Esta ação irá destruir todos os recursos criados pelo Terraform!"
echo "Isso inclui:"
echo "- S3 Bucket"
echo "- Lambda Function"
echo "- CloudWatch Log Groups"
echo "- IAM Roles e Policies"
echo "- EventBridge Rules"
echo ""
echo "❓ Tem certeza que deseja continuar? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "🗑️ Destruindo infraestrutura..."
    cd terraform
    terraform destroy -auto-approve
    echo "✅ Infraestrutura destruída com sucesso!"
    cd ..
else
    echo "❌ Operação cancelada pelo usuário"
    exit 1
fi

echo "🧹 Limpando arquivos temporários..."
rm -f lambda/binance-crawler.zip
rm -rf lambda/node_modules

echo "🎉 Limpeza concluída!" 