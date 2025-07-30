# API Cripto Prediction

API para predições de criptomoedas usando modelos de Machine Learning **já treinados** e salvos no S3.

## 🚀 Funcionalidades

- **Leitura automática de modelos** do S3 na inicialização
- **Predições em tempo real** usando dados mais recentes
- **Múltiplos tipos de modelo**: regressores e classificadores
- **Health checks** e monitoramento
- **Documentação automática** com Swagger/OpenAPI
- **Reload de modelos** sem reiniciar a API

## 🎭 Mock do Heterium (HET)

A API inclui um **mock temporário** para a criptomoeda **Heterium (HET)** que gera dados simulados para testes e demonstração.

### Características do Mock HET

- **Dados simulados**: 30 dias de dados históricos
- **Preço base**: $150 USD
- **Volatilidade**: 15%
- **Indicadores técnicos**: RSI, MACD, Bollinger Bands, etc.
- **Features completas**: Mais de 80 indicadores técnicos

### Como Usar o Mock

```bash
# Teste rápido do mock HET
cd api
./test-het-quick.sh

# Teste completo com Python
python test_het_mock.py http://localhost:8000

# Teste manual
curl http://localhost:8000/symbol/HET
```

### Exemplo de Resposta

```json
{
  "ativo": "HET",
  "timestamp": "2025-01-27T10:30:00",
  "modelos": {
    "regressor_gbr": {
      "predicao": 152.45,
      "modelo": "regressor_gbr",
      "tipo": "regressor",
      "versao": "20250729-2130"
    },
    "classifier_log": {
      "predicao": 1,
      "probabilidade": 0.75,
      "modelo": "classifier_log",
      "tipo": "classifier",
      "versao": "20250729-2130"
    }
  },
  "total_modelos": 2
}
```

### Logs do Mock

```
🎭 Usando dados mock para Heterium (HET)
🎭 Criando dados mock para Heterium...
✅ Dados mock criados para HET: 30 registros, 85 colunas
🔧 Preparando features de 30 registros...
📈 Features numéricas: 84 colunas
✅ Features preparadas: 84 colunas
🔮 Fazendo predição com regressor_gbr (tipo: regressor)
✅ Predição regressora: 152.45
```

## 📋 Pré-requisitos

- Python 3.9+
- AWS CLI configurado
- Acesso ao bucket S3 `criptos-data`
- **Modelos já treinados** salvos no S3 (pasta `models/`)

## 🛠️ Instalação e Configuração

### 1. Configurar AWS CLI

```bash
aws configure
```

Configure suas credenciais AWS com acesso ao bucket `criptos-data`.

### 2. Verificar Modelos Existentes no S3

```bash
# Verificar se o bucket existe
aws s3 ls s3://criptos-data

# Verificar modelos disponíveis
aws s3 ls s3://criptos-data/models/ --recursive
```

### 3. Deploy da API (Apenas Leitura)

```bash
# Navegar para a pasta da API
cd api

# Executar deploy (apenas leitura de modelos existentes)
./deploy-only.sh
```

### 4. Deploy Local Manual

```bash
# Navegar para a pasta da API
cd api

# Executar deploy local
./deploy-local.sh
```

### 5. Deploy com Docker

```bash
# Build da imagem
docker build -t cripto-prediction-api .

# Executar container
docker run -p 8000:8000 cripto-prediction-api
```

### 6. Deploy no Kubernetes

```bash
# Deploy completo
./deploy.sh

# Deploy simplificado
./deploy-simple.sh
```

## 📊 Endpoints

### Health Check
```
GET /health
```

### Listar Modelos
```
GET /models
```

### Fazer Predição
```
GET /symbol/{ativo}
```

Exemplo: `GET /symbol/BTC`

### Recarregar Modelos
```
GET /reload
```

## 🔧 Estrutura dos Modelos

A API **lê** modelos salvos no S3 com o seguinte padrão:

```
s3://criptos-data/models/
├── regressor_gbr_20250729-2130.joblib
├── regressor_lin_20250729-2130.joblib
└── classifier_log_20250729-2130.joblib
```

### Formato do Nome dos Modelos

- `{tipo}_{algoritmo}_{timestamp}.joblib`
- `tipo`: `regressor` ou `classifier`
- `algoritmo`: `gbr`, `lin`, `rf`, `log`, etc.
- `timestamp`: formato `YYYYMMDD-HHMMSS`

## 🧪 Testes

### Teste Automático

```bash
# Instalar requests se necessário
pip install requests

# Executar testes
python test_api.py http://localhost:8000
```

### Teste Manual

```bash
# Health check
curl http://localhost:8000/health

# Listar modelos
curl http://localhost:8000/models

# Fazer predição
curl http://localhost:8000/symbol/BTC

# Recarregar modelos
curl http://localhost:8000/reload
```

## 📝 Logs e Debug

A API possui logs detalhados para debug:

```bash
# Ver logs da API
docker logs <container_id>

# Ou se rodando localmente, os logs aparecem no terminal
```

### Logs Importantes

- `🚀 Iniciando carregamento de todos os modelos...`
- `✅ Modelo carregado: {nome_do_modelo}`
- `🔮 Fazendo predição com {modelo}`
- `✅ Predição regressora: {valor}`

## 🔍 Troubleshooting

### Problema: "Nenhum modelo carregado"

**Solução:**
1. Verificar se os modelos existem no S3:
   ```bash
   aws s3 ls s3://criptos-data/models/ --recursive
   ```

2. Verificar se os nomes seguem o padrão esperado:
   ```
   regressor_gbr_20250729-2130.joblib
   ```

3. Verificar permissões AWS:
   ```bash
   aws sts get-caller-identity
   ```

### Problema: "Nenhum dado encontrado para o símbolo"

**Solução:**
1. Verificar se existem dados no S3:
   ```bash
   aws s3 ls s3://criptos-data/data/BTC/
   ```

2. Verificar formato dos dados (CSV com colunas numéricas)

### Problema: "Erro na predição"

**Solução:**
1. Verificar se as features estão corretas
2. Verificar se o modelo foi treinado com as mesmas features
3. Verificar logs detalhados da API

## 📚 Documentação da API

Acesse a documentação interativa em:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   ModelManager  │    │   S3 Bucket     │
│                 │    │                 │    │                 │
│ - /health       │◄──►│ - Load Models   │◄──►│ - models/*.joblib│
│ - /models       │    │ - Cache Models  │    │ - data/*.csv    │
│ - /symbol/{id}  │    │ - Predict       │    │                 │
│ - /reload       │    └─────────────────┘    └─────────────────┘
└─────────────────┘
```

## 🔄 Fluxo de Dados

1. **Inicialização**: API carrega modelos existentes do S3
2. **Requisição**: Cliente solicita predição para um símbolo
3. **Dados**: API busca dados mais recentes do S3
4. **Features**: Prepara features dos dados
5. **Predição**: Executa predição com todos os modelos carregados
6. **Resposta**: Retorna predições formatadas

## 📈 Monitoramento

### Métricas Importantes

- **Modelos carregados**: Número de modelos em memória
- **Tempo de resposta**: Latência das predições
- **Taxa de erro**: Predições que falharam
- **Uso de memória**: Consumo de RAM dos modelos

### Health Checks

```bash
# Verificar status
curl http://localhost:8000/health

# Resposta esperada:
{
  "status": "healthy",
  "models_loaded": true,
  "total_models": 3,
  "models": ["regressor_gbr", "regressor_lin", "classifier_log"],
  "versions": {"regressor_gbr": "20250729-2130"}
}
```

## 🚀 Deploy em Produção

### Variáveis de Ambiente

```bash
export AWS_DEFAULT_REGION=us-east-1
export BUCKET_NAME=criptos-data
export LOG_LEVEL=INFO
```

### Kubernetes

```bash
# Aplicar deployment
kubectl apply -f k8s/deployment.yaml

# Aplicar ingress
kubectl apply -f k8s/ingress.yaml

# Verificar status
kubectl get pods
kubectl get services
kubectl get ingress
```

### Docker

```bash
# Build
docker build -t cripto-prediction-api .

# Run
docker run -p 8000:8000 \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -e BUCKET_NAME=criptos-data \
  cripto-prediction-api
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. 