# 🚀 Crawler da Binance

Um sistema completo de crawler para coletar dados de todos os ativos disponíveis na Binance, construído com Terraform, AWS Lambda e Node.js.

## 📋 Funcionalidades

- **Coleta Automática**: Executa automaticamente a cada hora
- **Dados Completos**: Coleta informações de todos os símbolos ativos
- **Armazenamento**: Salva dados no S3 com estrutura organizada
- **Monitoramento**: Logs detalhados no CloudWatch
- **Escalabilidade**: Processamento em lotes para evitar sobrecarga da API

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EventBridge   │───▶│   Lambda        │───▶│   DynamoDB      │
│   (Scheduler)   │    │   (Crawler)     │    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   CloudWatch    │
                       │   (Logs)        │
                       └─────────────────┘
```

## 📦 Componentes

### Terraform (`terraform/`)
- **S3**: Armazenamento dos dados dos ativos
- **Lambda**: Função para coleta de dados
- **IAM**: Roles e policies necessárias
- **EventBridge**: Agendamento de execução
- **CloudWatch**: Logs e monitoramento

### Lambda (`lambda/`)
- **Node.js**: Runtime da função
- **AWS SDK**: Integração com serviços AWS
- **HTTPS**: Requisições para API da Binance
- **Processamento em lotes**: Para evitar rate limits

### Scripts (`scripts/`)
- **deploy.sh**: Script de deploy automatizado
- **destroy.sh**: Script para destruir infraestrutura
- **monitor.sh**: Script para monitoramento

## 🚀 Deploy

### Pré-requisitos

1. **AWS CLI** configurado com credenciais
2. **Terraform** instalado
3. **Node.js** instalado
4. **Bash** (para scripts)

### Deploy Automatizado

```bash
# Tornar scripts executáveis
chmod +x scripts/*.sh

# Executar deploy
./scripts/deploy.sh
```

### Deploy Manual

```bash
# 1. Instalar dependências do Lambda
cd lambda
npm install
npm run package
cd ..

# 2. Deploy do Terraform
cd terraform
terraform init
terraform plan
terraform apply
cd ..
```

## 📊 Monitoramento

### Ver Logs em Tempo Real
```bash
aws logs tail /aws/lambda/binance-crawler --follow
```

### Executar Manualmente
```bash
aws lambda invoke --function-name binance-crawler --payload '{}' response.json
```

### Usar Script de Monitoramento
```bash
./scripts/monitor.sh
```

## 📈 Dados Coletados

Para cada símbolo, o crawler coleta:

### Ticker 24h
- Preço atual
- Volume de negociação
- Variação percentual
- Preço máximo/mínimo

### Ticker Price
- Preço atual do ativo

### Order Book
- Melhores ofertas de compra/venda
- Profundidade do mercado

### Metadados
- Símbolo
- Timestamp da coleta
- Status do ativo

## 🗄️ Estrutura do S3

### Organização dos Dados
```
s3://bucket-name/
├── data/
│   ├── 2024-01-15/
│   │   ├── BTCUSDT/
│   │   │   ├── 2024-01-15T10-30-00-000Z.json
│   │   │   ├── 2024-01-15T11-30-00-000Z.json
│   │   │   └── ...
│   │   ├── ETHUSDT/
│   │   │   ├── 2024-01-15T10-30-00-000Z.json
│   │   │   └── ...
│   │   └── ...
│   ├── 2024-01-16/
│   │   └── ...
│   └── ...
```

### Estrutura dos Arquivos JSON
```json
{
  "symbol": "BTCUSDT",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "ticker24hr": { /* dados do ticker 24h */ },
  "tickerPrice": { /* dados do preço atual */ },
  "orderBook": { /* dados do order book */ }
}
```

## ⚙️ Configuração

### Variáveis do Terraform

Edite `terraform/variables.tf` para personalizar:

```hcl
variable "aws_region" {
  default = "us-east-1"  # Sua região AWS
}

variable "environment" {
  default = "production"
}
```

### Configuração do Lambda

Edite `lambda/index.js` para ajustar:

- **Batch Size**: Número de símbolos processados por lote
- **Delay**: Tempo entre lotes (evitar rate limits)
- **Timeout**: Tempo máximo de execução

## 🔧 Manutenção

### Atualizar Lambda
```bash
cd lambda
npm install
npm run package
cd ../terraform
terraform apply
```

### Destruir Infraestrutura
```bash
./scripts/destroy.sh
```

### Verificar Status
```bash
# Status do Lambda
aws lambda get-function --function-name binance-crawler

# Status do DynamoDB
aws dynamodb describe-table --table-name binance-assets

# Logs recentes
aws logs describe-log-streams --log-group-name /aws/lambda/binance-crawler
```

## 📊 Análise de Dados

### Consultas Úteis no S3

```bash
# Listar todos os objetos do bucket
aws s3 ls s3://bucket-name --recursive

# Listar dados de um símbolo específico
aws s3 ls s3://bucket-name/data/2024-01-15/BTCUSDT/

# Baixar dados de um símbolo
aws s3 cp s3://bucket-name/data/2024-01-15/BTCUSDT/2024-01-15T10-30-00-000Z.json ./

# Listar símbolos disponíveis hoje
aws s3 ls s3://bucket-name/data/$(date +%Y-%m-%d)/ --recursive | cut -d'/' -f4 | sort | uniq

# Contar total de objetos
aws s3 ls s3://bucket-name --recursive | wc -l
```

## 🚨 Troubleshooting

### Erro de Rate Limit
- Aumentar delay entre lotes
- Reduzir batch size
- Verificar logs para identificar símbolos problemáticos

### Timeout do Lambda
- Aumentar timeout no Terraform
- Reduzir batch size
- Otimizar código para processamento mais rápido

### Erro de Permissões
- Verificar IAM roles e policies
- Confirmar credenciais AWS
- Verificar logs do CloudWatch

## 📝 Logs Importantes

### Logs de Sucesso
```
INFO: Iniciando crawler da Binance...
INFO: Total de símbolos encontrados: 1500
INFO: Símbolos ativos: 1200
INFO: Processando lote 1/240
INFO: Dados salvos para BTCUSDT
INFO: Processamento concluído: - Sucessos: 1200 - Falhas: 0
```

### Logs de Erro
```
ERROR: Erro ao obter informações do símbolo INVALIDPAIR: Request failed
ERROR: Erro ao salvar dados para BTCUSDT: AccessDenied
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🆘 Suporte

Para suporte ou dúvidas:
- Abra uma issue no repositório
- Consulte a documentação da AWS
- Verifique os logs do CloudWatch

---

**Desenvolvido para o Tech Challenge Fase 4** 🚀 