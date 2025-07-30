# 🚀 Cripto Prediction API

API FastAPI para predições de criptomoedas usando modelos ML treinados no AWS Glue.

## 📋 Funcionalidades

- **Carregamento automático** de modelos .joblib do S3
- **Predições em tempo real** para qualquer ativo
- **Health checks** e monitoramento
- **Deploy no EKS** com alta disponibilidade
- **Documentação automática** (Swagger/OpenAPI)

## 🏗️ Arquitetura

```
EKS Cluster → FastAPI Pods → S3 Models → Predictions
```

### Componentes:
- **FastAPI**: Framework web para a API
- **EKS**: Kubernetes gerenciado pela AWS
- **S3**: Armazenamento dos modelos treinados
- **Docker**: Containerização da aplicação

## 📁 Estrutura do Projeto

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app + endpoints
│   ├── models.py        # Engine de predições
│   └── utils.py         # Gerenciamento de modelos
├── k8s/
│   └── deployment.yaml  # Kubernetes deployment
├── terraform/
│   ├── main.tf         # Infraestrutura EKS
│   ├── variables.tf    # Variáveis
│   └── outputs.tf      # Outputs
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🚀 Endpoints

### 1. **GET /** - Root
```json
{
  "message": "Cripto Prediction API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

### 2. **GET /health** - Health Check
```json
{
  "status": "healthy",
  "models_loaded": true,
  "total_models": 5,
  "models": ["regressor_rf", "regressor_gbr", "regressor_lin", "classifier_rf", "classifier_log"],
  "versions": {
    "regressor_rf": "20250729-2130",
    "classifier_rf": "20250729-2130"
  }
}
```

### 3. **GET /models** - Lista Modelos
```json
{
  "total_models": 5,
  "models": ["regressor_rf", "regressor_gbr", "regressor_lin", "classifier_rf", "classifier_log"],
  "versions": {
    "regressor_rf": "20250729-2130"
  },
  "last_loaded": "2025-07-29T21:30:00Z"
}
```

### 4. **GET /symbol/{ativo}** - Predições
```json
{
  "ativo": "BTC",
  "timestamp": "2025-07-29T21:30:00Z",
  "modelos": {
    "regressor_rf": {
      "predicao": 45000.50,
      "modelo": "regressor_rf",
      "tipo": "regressor",
      "versao": "20250729-2130"
    },
    "classifier_rf": {
      "predicao": 1,
      "probabilidade": 0.75,
      "modelo": "classifier_rf",
      "tipo": "classifier",
      "versao": "20250729-2130"
    }
  },
  "total_modelos": 5
}
```

### 5. **GET /reload** - Recarregar Modelos
```json
{
  "message": "Modelos recarregados com sucesso",
  "total_models": 5,
  "models": ["regressor_rf", "regressor_gbr", "regressor_lin", "classifier_rf", "classifier_log"]
}
```

## 🛠️ Deploy

### 1. **Build da Imagem Docker**
```bash
cd api
docker build -t cripto-prediction-api:latest .
```

### 2. **Deploy no EKS**
```bash
# Configurar kubectl
aws eks update-kubeconfig --region us-east-1 --name cripto-prediction-cluster

# Aplicar deployment
kubectl apply -f k8s/deployment.yaml

# Verificar status
kubectl get pods
kubectl get services
```

### 3. **Terraform (Infraestrutura)**
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## 🔧 Configuração

### Variáveis de Ambiente:
- `AWS_DEFAULT_REGION`: Região AWS (us-east-1)
- `BUCKET_NAME`: Nome do bucket S3 (criptos-data)

### Recursos Kubernetes:
- **CPU**: 500m request, 1000m limit
- **Memory**: 2Gi request, 4Gi limit
- **Replicas**: 2 pods para alta disponibilidade

## 📊 Monitoramento

### Health Checks:
- **Liveness**: `/health` a cada 30s
- **Readiness**: `/health` a cada 10s
- **Initial Delay**: 60s para liveness, 30s para readiness

### Logs:
```bash
kubectl logs -f deployment/cripto-prediction-api
```

### Métricas:
- Modelos carregados
- Tempo de resposta das predições
- Erros de predição

## 🔒 Segurança

- **IAM Roles**: Acesso específico ao S3
- **Non-root user**: Container roda como usuário não-root
- **Resource limits**: Limites de CPU/memory
- **Health checks**: Monitoramento automático

## 🚀 Uso

### Exemplo de Predição:
```bash
curl "http://your-api-endpoint/symbol/BTC"
```

### Verificar Status:
```bash
curl "http://your-api-endpoint/health"
```

### Documentação Interativa:
```
http://your-api-endpoint/docs
```

## 📈 Escalabilidade

- **Horizontal**: Múltiplas réplicas no EKS
- **Vertical**: Ajuste de recursos conforme necessário
- **Auto-scaling**: Baseado em CPU/memory
- **Load balancing**: Distribuição automática de carga

## 🔄 Atualizações

### Rolling Update:
```bash
kubectl set image deployment/cripto-prediction-api cripto-prediction-api=new-image:tag
```

### Rollback:
```bash
kubectl rollout undo deployment/cripto-prediction-api
```

## 🐛 Troubleshooting

### Modelos não carregam:
1. Verificar permissões S3
2. Verificar logs do pod
3. Verificar se arquivos existem no bucket

### API não responde:
1. Verificar health check
2. Verificar recursos (CPU/memory)
3. Verificar conectividade de rede

### Predições com erro:
1. Verificar formato dos dados de entrada
2. Verificar se modelos estão carregados
3. Verificar logs de erro 