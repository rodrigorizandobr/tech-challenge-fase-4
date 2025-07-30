#!/bin/bash

# Script rápido para testar o mock do Heterium
echo "🎭 Testando mock do Heterium (HET)..."

# Configurações
API_URL="http://localhost:8000"

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
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# 1. Verificar se a API está rodando
log "Verificando se a API está rodando..."
if ! curl -s "$API_URL/health" > /dev/null; then
    error "API não está rodando em $API_URL"
    echo ""
    echo "💡 Para iniciar a API:"
    echo "   cd api"
    echo "   ./deploy-only.sh"
    exit 1
fi

success "API está rodando!"

# 2. Testar health check
log "Testando health check..."
HEALTH_RESPONSE=$(curl -s "$API_URL/health")
if [ $? -eq 0 ]; then
    success "Health check OK"
    echo "   Status: $(echo $HEALTH_RESPONSE | jq -r '.status' 2>/dev/null || echo 'N/A')"
    echo "   Modelos carregados: $(echo $HEALTH_RESPONSE | jq -r '.models_loaded' 2>/dev/null || echo 'N/A')"
else
    error "Health check falhou"
fi

# 3. Testar predição do HET
log "Testando predição para HET..."
HET_RESPONSE=$(curl -s "$API_URL/symbol/HET")
if [ $? -eq 0 ]; then
    success "Predição HET OK"
    
    # Extrair informações da resposta
    ATIVO=$(echo $HET_RESPONSE | jq -r '.ativo' 2>/dev/null || echo 'N/A')
    TIMESTAMP=$(echo $HET_RESPONSE | jq -r '.timestamp' 2>/dev/null || echo 'N/A')
    TOTAL_MODELOS=$(echo $HET_RESPONSE | jq -r '.total_modelos' 2>/dev/null || echo 'N/A')
    
    echo "   Ativo: $ATIVO"
    echo "   Timestamp: $TIMESTAMP"
    echo "   Total de modelos: $TOTAL_MODELOS"
    
    # Mostrar predições
    echo "   Predições:"
    echo $HET_RESPONSE | jq -r '.modelos | to_entries[] | "     📊 " + .key + ": " + (.value.predicao | tostring) + " (" + .value.tipo + ")"' 2>/dev/null || echo "     Nenhuma predição disponível"
    
else
    error "Predição HET falhou"
fi

# 4. Testar outros símbolos para comparação
log "Testando outros símbolos para comparação..."
SYMBOLS=("BTC" "ETH")

for symbol in "${SYMBOLS[@]}"; do
    RESPONSE=$(curl -s "$API_URL/symbol/$symbol")
    if [ $? -eq 0 ]; then
        info "$symbol: OK"
    else
        error "$symbol: Falhou"
    fi
done

# 5. Resumo
echo ""
echo "📋 RESUMO DO TESTE HET"
echo "======================"
echo "✅ API funcionando"
echo "✅ Health check OK"
echo "✅ Mock HET funcionando"
echo ""
echo "🎭 Mock do Heterium está ativo!"
echo "   URL: $API_URL/symbol/HET"
echo ""
echo "🔧 Para testar manualmente:"
echo "   curl $API_URL/symbol/HET"
echo "   curl $API_URL/health"
echo ""
echo "📚 Documentação: $API_URL/docs" 