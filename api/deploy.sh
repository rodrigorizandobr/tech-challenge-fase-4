#!/bin/bash

# Script de Deploy Automatizado para API Cripto Prediction
set -e

echo "🚀 Iniciando deploy da API Cripto Prediction..."

# Configurações
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="416759445527"
ECR_REPOSITORY="cripto-prediction-api"
CLUSTER_NAME="cripto-prediction-cluster"
IMAGE_TAG="latest"

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

# 3. Verificar se Docker está rodando
log "Verificando Docker..."
if ! docker info &> /dev/null; then
    error "Docker não está rodando."
fi

# 4. Criar ECR repository se não existir
log "Verificando/criando ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION &> /dev/null || {
    log "Criando ECR repository..."
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
}

# 5. Login no ECR
log "Fazendo login no ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 6. Build da imagem Docker
log "Fazendo build da imagem Docker..."
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .

# 7. Tag da imagem para ECR
log "Tagueando imagem para ECR..."
docker tag $ECR_REPOSITORY:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# 8. Push para ECR
log "Fazendo push para ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# 9. Configurar kubectl para o cluster EKS
log "Configurando kubectl para o cluster EKS..."
aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME

# 10. Verificar se o cluster está acessível
log "Verificando acesso ao cluster..."
if ! kubectl cluster-info &> /dev/null; then
    error "Não foi possível acessar o cluster EKS. Verifique se o cluster existe e está acessível."
fi

# 11. Instalar AWS Load Balancer Controller se não estiver instalado
log "Verificando AWS Load Balancer Controller..."
if ! kubectl get deployment -n kube-system aws-load-balancer-controller &> /dev/null; then
    warning "AWS Load Balancer Controller não encontrado. Instalando..."
    
    # Instalar Helm se não estiver instalado
    if ! command -v helm &> /dev/null; then
        log "Instalando Helm..."
        curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    fi
    
    # Adicionar repositório Helm
    helm repo add eks https://aws.github.io/eks-charts
    helm repo update
    
    # Instalar AWS Load Balancer Controller
    helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName=$CLUSTER_NAME \
        --set serviceAccount.create=false \
        --set serviceAccount.name=aws-load-balancer-controller
fi

# 12. Aplicar deployment
log "Aplicando deployment Kubernetes..."
kubectl apply -f k8s/deployment.yaml

# 13. Aplicar ingress
log "Aplicando Ingress..."
kubectl apply -f k8s/ingress.yaml

# 14. Aguardar pods ficarem prontos
log "Aguardando pods ficarem prontos..."
kubectl wait --for=condition=ready pod -l app=cripto-prediction-api --timeout=300s

# 15. Obter URL do Load Balancer
log "Obtendo URL do Load Balancer..."
sleep 30  # Aguardar ALB ser criado

INGRESS_HOST=$(kubectl get ingress cripto-prediction-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

if [ -z "$INGRESS_HOST" ]; then
    warning "Load Balancer ainda não está pronto. Verifique em alguns minutos:"
    echo "kubectl get ingress cripto-prediction-ingress"
else
    log "✅ Deploy concluído com sucesso!"
    echo ""
    echo "🌐 URL da API: https://$INGRESS_HOST"
    echo "📊 Health Check: https://$INGRESS_HOST/health"
    echo "📚 Documentação: https://$INGRESS_HOST/docs"
    echo "🔍 Predição exemplo: https://$INGRESS_HOST/symbol/BTC"
    echo ""
    echo "📋 Comandos úteis:"
    echo "  kubectl get pods"
    echo "  kubectl logs -f deployment/cripto-prediction-api"
    echo "  kubectl get ingress"
    echo "  kubectl get services"
fi

log "Deploy concluído! 🎉" 