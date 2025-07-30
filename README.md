# 🚀 Tech Challenge Fase 4 - Sistema de Predição de Criptomoedas

Sistema completo de Machine Learning para predição de criptomoedas, composto por três componentes principais: **crawler de dados**, **treinamento de modelos** e **API de predições**.

## 📋 Visão Geral do Projeto

Este projeto implementa um pipeline completo de Machine Learning para análise e predição de criptomoedas:

1. **🕷️ Crawler (cripto-compare-extractor)**: Coleta dados históricos de criptomoedas
2. **🤖 Modelos (models)**: Treina modelos estatísticos com os dados coletados
3. **🌐 API (api)**: Disponibiliza predições via REST API

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Crawler       │    │   Modelos       │    │   API           │
│                 │    │                 │    │                 │
│ • Coleta dados  │───►│ • Treina ML     │───►│ • Predições     │
│ • S3 Storage    │    │ • S3 Models     │    │ • REST API      │
│ • Lambda        │    │ • Glue Jobs     │    │ • FastAPI       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🕷️ Cripto Compare Extractor (Crawler)

### 📊 Funcionalidades

- **Coleta automática** de dados históricos de criptomoedas
- **Integração com CryptoCompare API**
- **Armazenamento no S3** para processamento posterior
- **Execução via AWS Lambda** para automação
- **Monitoramento** e logs detalhados

### 🏗️ Arquitetura

```
AWS Lambda → CryptoCompare API → S3 Storage → Processamento
```

### 📁 Estrutura

```
cripto-compare-extractor/
├── lambda/
│   ├── index.js          # Função principal do Lambda
│   ├── config.js         # Configurações
│   └── package.json      # Dependências Node.js
├── scripts/
│   ├── deploy.sh         # Deploy do Lambda
│   ├── destroy.sh        # Remoção da infraestrutura
│   └── monitor.sh        # Monitoramento
├── terraform/
│   ├── main.tf          # Infraestrutura AWS
│   ├── variables.tf     # Variáveis
│   └── outputs.tf       # Outputs
└── README.md            # Documentação específica
```

### 🚀 Como Usar

```bash
# Navegar para o crawler
cd cripto-compare-extractor

# Deploy da infraestrutura
./scripts/deploy.sh

# Monitorar execução
./scripts/monitor.sh

# Verificar dados coletados
aws s3 ls s3://criptos-data/data/
```

### 📈 Dados Coletados

- **Preços**: abertura, fechamento, máximo, mínimo
- **Volumes**: volume de negociação
- **Market Cap**: capitalização de mercado
- **Timestamps**: dados históricos diários
- **Múltiplas criptomoedas**: BTC, ETH, ADA, etc.

## 🤖 Models (Treinamento de Modelos)

### 📊 Funcionalidades

- **Feature Engineering**: Preparação de dados para ML
- **Treinamento de Modelos**: Regressores e classificadores
- **AWS Glue Jobs**: Processamento distribuído
- **Armazenamento de Modelos**: S3 com versionamento
- **Pipeline Automatizado**: Trigger por novos dados

### 🏗️ Arquitetura

```
S3 Data → Glue Feature Engineering → Glue Model Training → S3 Models
```

### 📁 Estrutura

```
models/
├── feature_engineering.py    # Preparação de features
├── train_models_glue_simple.py  # Treinamento de modelos
├── glue_trigger.py          # Trigger para novos dados
├── terraform/
│   ├── main.tf             # Infraestrutura Glue
│   ├── variables.tf        # Variáveis
│   └── outputs.tf          # Outputs
└── README.md               # Documentação específica
```

### 🚀 Como Usar

```bash
# Navegar para models
cd models

# Deploy da infraestrutura
terraform init
terraform apply

# Verificar modelos treinados
aws s3 ls s3://criptos-data/models/
```

### 🤖 Modelos Treinados

#### Regressores
- **Gradient Boosting Regressor**: Predição de preços
- **Linear Regression**: Análise de tendências
- **Random Forest**: Robustez em dados complexos

#### Classificadores
- **Logistic Regression**: Classificação de direção
- **Random Forest Classifier**: Padrões de mercado

### 📊 Features Utilizadas

- **Indicadores Técnicos**: RSI, MACD, Bollinger Bands
- **Médias Móveis**: SMA, EMA, Hull Moving Average
- **Osciladores**: Stochastic, Williams %R, CCI
- **Volumes**: OBV, Volume Momentum
- **Tendências**: ADX, Momentum, ROC

## 🌐 API (Predições)

### 📊 Funcionalidades

- **Leitura de Modelos**: Carregamento automático do S3
- **Predições em Tempo Real**: Consulta por símbolo
- **Mock do Heterium**: Dados simulados para testes
- **Health Checks**: Monitoramento da API
- **Documentação Automática**: Swagger/OpenAPI

### 🏗️ Arquitetura

```
FastAPI → ModelManager → S3 Models → Predictions
```

### 📁 Estrutura

```
api/
├── app/
│   ├── main.py            # FastAPI application
│   ├── models.py          # Engine de predições
│   ├── utils.py           # Gerenciamento de modelos
│   └── simple_main.py     # Versão simplificada
├── k8s/
│   ├── deployment.yaml    # Kubernetes deployment
│   └── ingress.yaml       # Ingress configuration
├── terraform/
│   ├── main.tf           # Infraestrutura EKS
│   ├── variables.tf      # Variáveis
│   └── outputs.tf        # Outputs
├── deploy-local.sh        # Deploy local
├── deploy-only.sh         # Deploy para leitura
├── test_het_mock.py       # Testes do mock
└── README.md             # Documentação específica
```

### 🚀 Como Usar

```bash
# Navegar para API
cd api

# Deploy local
./deploy-local.sh

# Testar mock do Heterium
./test-het-quick.sh

# Testes completos
python test_het_mock.py http://localhost:8000
```

### 📊 Endpoints

#### Health Check
```bash
curl https://a88fmc3yc5.execute-api.us-east-1.amazonaws.com/prod/health
```

#### Listar Modelos
```bash
curl https://a88fmc3yc5.execute-api.us-east-1.amazonaws.com/prod/models
```

#### Fazer Predição
```bash
curl https://a88fmc3yc5.execute-api.us-east-1.amazonaws.com/prod/symbol/BTC
curl https://a88fmc3yc5.execute-api.us-east-1.amazonaws.com/prod/symbol/HET  # Mock do Heterium
```

#### Recarregar Modelos
```bash
curl https://a88fmc3yc5.execute-api.us-east-1.amazonaws.com/prod/reload
```

## 🔄 Fluxo Completo do Sistema

### 1. **Coleta de Dados**
```bash
# Crawler coleta dados automaticamente
AWS Lambda → CryptoCompare API → S3 Storage
```

### 2. **Processamento e Treinamento**
```bash
# Glue Jobs processam e treinam modelos
S3 Data → Glue Feature Engineering → Glue Model Training → S3 Models
```

### 3. **Predições via API**
```bash
# API carrega modelos e faz predições
FastAPI → ModelManager → S3 Models → Predictions
```

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python**: FastAPI, scikit-learn, pandas, numpy
- **Node.js**: AWS Lambda functions
- **Terraform**: Infraestrutura como código

### Cloud (AWS)
- **S3**: Armazenamento de dados e modelos
- **Lambda**: Execução serverless do crawler
- **Glue**: Processamento de dados e ML
- **EKS**: Orquestração de containers (opcional)

### Machine Learning
- **scikit-learn**: Modelos de ML
- **pandas**: Manipulação de dados
- **numpy**: Computação numérica
- **joblib**: Serialização de modelos

## 🚀 Deploy Completo

### 1. **Configurar AWS CLI**
```bash
aws configure
```

### 2. **Deploy do Crawler**
```bash
cd cripto-compare-extractor
./scripts/deploy.sh
```

### 3. **Deploy dos Modelos**
```bash
cd models
terraform init
terraform apply
```

### 4. **Deploy da API**
```bash
cd api
./deploy-local.sh
```
 IMAGEM DA ARQUITETURA NA RAIZ DO REPOSITÓRIO