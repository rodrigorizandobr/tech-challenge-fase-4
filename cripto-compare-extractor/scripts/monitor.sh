#!/bin/bash

# Script para monitorar o crawler da Binance
set -e

echo "📊 Monitor do Crawler da Binance"
echo "================================"

# Função para mostrar logs do CloudWatch
show_logs() {
    echo "📝 Últimos logs do Lambda:"
    aws logs tail /aws/lambda/binance-crawler --since 1h --follow
}

# Função para mostrar estatísticas do S3
show_stats() {
    echo "📊 Estatísticas do S3:"
    
    # Obter nome do bucket
    bucket_name=$(aws s3 ls | grep binance-crawler-data | awk '{print $3}' | head -1)
    
    if [ -z "$bucket_name" ]; then
        echo "❌ Bucket S3 não encontrado"
        return
    fi
    
    echo "Bucket: $bucket_name"
    
    # Contar total de objetos
    total_objects=$(aws s3 ls s3://$bucket_name --recursive | wc -l)
    echo "Total de objetos: $total_objects"
    
    # Mostrar estrutura de pastas
    echo ""
    echo "📁 Estrutura de pastas:"
    aws s3 ls s3://$bucket_name/data/ --recursive | head -10
    
    # Mostrar últimos 5 objetos
    echo ""
    echo "📋 Últimos 5 objetos:"
    aws s3 ls s3://$bucket_name --recursive | tail -5
}

# Função para executar o Lambda manualmente
run_lambda() {
    echo "🚀 Executando Lambda manualmente..."
    aws lambda invoke \
        --function-name binance-crawler \
        --payload '{}' \
        response.json
    
    echo "✅ Lambda executado! Resposta:"
    cat response.json
    rm response.json
}

# Menu principal
while true; do
    echo ""
    echo "Escolha uma opção:"
    echo "1) Ver logs em tempo real"
    echo "2) Ver estatísticas do DynamoDB"
    echo "3) Executar Lambda manualmente"
    echo "4) Sair"
    echo ""
    read -p "Opção: " choice
    
    case $choice in
        1)
            show_logs
            ;;
        2)
            show_stats
            ;;
        3)
            run_lambda
            ;;
        4)
            echo "👋 Saindo..."
            exit 0
            ;;
        *)
            echo "❌ Opção inválida"
            ;;
    esac
done 