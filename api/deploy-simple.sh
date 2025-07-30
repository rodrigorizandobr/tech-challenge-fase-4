#!/bin/bash

# Script de Deploy Simplificado (sem Docker)
set -e

echo "🚀 Iniciando deploy simplificado da API Cripto Prediction..."

# Configurações
AWS_REGION="us-east-1"
CLUSTER_NAME="cripto-prediction-cluster"

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

# 2. Verificar se kubectl está instalado
log "Verificando kubectl..."
if ! command -v kubectl &> /dev/null; then
    error "kubectl não está instalado."
fi

# 3. Configurar kubectl para o cluster EKS
log "Configurando kubectl para o cluster EKS..."
aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME

# 4. Verificar se o cluster está acessível
log "Verificando acesso ao cluster..."
if ! kubectl cluster-info &> /dev/null; then
    error "Não foi possível acessar o cluster EKS. Verifique se o cluster existe e está acessível."
fi

# 5. Criar namespace se não existir
log "Criando namespace..."
kubectl create namespace cripto-prediction --dry-run=client -o yaml | kubectl apply -f -

# 6. Criar ConfigMap com o código Python
log "Criando ConfigMap com o código da API..."
kubectl create configmap api-code --from-file=app/ -n cripto-prediction --dry-run=client -o yaml | kubectl apply -f -

# 7. Criar deployment simplificado
log "Criando deployment simplificado..."
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cripto-prediction-api
  namespace: cripto-prediction
  labels:
    app: cripto-prediction-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cripto-prediction-api
  template:
    metadata:
      labels:
        app: cripto-prediction-api
    spec:
      containers:
      - name: cripto-prediction-api
        image: python:3.9-slim
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "1000m"
        env:
        - name: AWS_DEFAULT_REGION
          value: "us-east-1"
        - name: BUCKET_NAME
          value: "criptos-data"
        command: ["/bin/bash"]
        args:
        - -c
        - |
          apt-get update && apt-get install -y curl
          pip install fastapi uvicorn boto3 pandas numpy scikit-learn joblib python-multipart pydantic
          mkdir -p /app
          cp -r /api-code/* /app/
          cd /app
          python -m uvicorn simple_main:app --host 0.0.0.0 --port 8000
        volumeMounts:
        - name: api-code
          mountPath: /api-code
          readOnly: true
      volumes:
      - name: api-code
        configMap:
          name: api-code
---
apiVersion: v1
kind: Service
metadata:
  name: cripto-prediction-service
  namespace: cripto-prediction
  labels:
    app: cripto-prediction-api
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  selector:
    app: cripto-prediction-api
EOF

# 8. Aguardar pods ficarem prontos
log "Aguardando pods ficarem prontos..."
kubectl wait --for=condition=ready pod -l app=cripto-prediction-api -n cripto-prediction --timeout=300s

# 9. Obter URL do Load Balancer
log "Obtendo URL do Load Balancer..."
sleep 30  # Aguardar Load Balancer ser criado

SERVICE_HOST=$(kubectl get service cripto-prediction-service -n cripto-prediction -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

if [ -z "$SERVICE_HOST" ]; then
    warning "Load Balancer ainda não está pronto. Verifique em alguns minutos:"
    echo "kubectl get service -n cripto-prediction"
else
    log "✅ Deploy concluído com sucesso!"
    echo ""
    echo "🌐 URL da API: http://$SERVICE_HOST"
    echo "📊 Health Check: http://$SERVICE_HOST/health"
    echo "📚 Documentação: http://$SERVICE_HOST/docs"
    echo "🔍 Predição exemplo: http://$SERVICE_HOST/symbol/BTC"
    echo ""
    echo "📋 Comandos úteis:"
    echo "  kubectl get pods -n cripto-prediction"
    echo "  kubectl logs -f deployment/cripto-prediction-api -n cripto-prediction"
    echo "  kubectl get service -n cripto-prediction"
fi

log "Deploy concluído! 🎉" 