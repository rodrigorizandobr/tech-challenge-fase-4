#!/bin/bash

# Script rápido para verificar modelos no S3
echo "🔍 Verificação rápida de modelos no S3..."

BUCKET_NAME="criptos-data"

# Verificar bucket
if aws s3 ls s3://$BUCKET_NAME &> /dev/null; then
    echo "✅ Bucket encontrado: $BUCKET_NAME"
else
    echo "❌ Bucket não encontrado: $BUCKET_NAME"
    exit 1
fi

# Verificar modelos
MODEL_COUNT=$(aws s3 ls s3://$BUCKET_NAME/models/ --recursive 2>/dev/null | grep -c ".joblib" || echo "0")

echo "📊 Modelos encontrados: $MODEL_COUNT"

if [ $MODEL_COUNT -gt 0 ]; then
    echo "✅ Modelos disponíveis:"
    aws s3 ls s3://$BUCKET_NAME/models/ --recursive | grep ".joblib" | while read -r line; do
        echo "   📁 $line"
    done
    echo ""
    echo "🚀 Para fazer deploy da API:"
    echo "   ./deploy-only.sh"
else
    echo "❌ Nenhum modelo encontrado"
    echo ""
    echo "💡 Opções:"
    echo "   1. Fazer upload de modelos para s3://$BUCKET_NAME/models/"
    echo "   2. Usar API em modo simulado"
    echo "   3. Treinar novos modelos"
fi 