# 📋 Documentação Técnica - Crawler da Binance

## 🏗️ Arquitetura Detalhada

### Componentes da Infraestrutura

#### 1. S3 Bucket (`binance-crawler-data-*`)
- **Nome**: Único com sufixo aleatório
- **Versionamento**: Habilitado
- **Lifecycle**: Configurado para arquivamento automático
- **Estrutura**: Organizada por data/símbolo

**Estrutura dos Dados:**
```
s3://bucket-name/data/2024-01-15/BTCUSDT/2024-01-15T10-30-00-000Z.json
```

**Conteúdo do arquivo JSON:**
```json
{
  "symbol": "BTCUSDT",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "ticker24hr": {
    "symbol": "BTCUSDT",
    "priceChange": "1234.56",
    "priceChangePercent": "2.5",
    "weightedAvgPrice": "45678.90",
    "prevClosePrice": "44444.34",
    "lastPrice": "45678.90",
    "lastQty": "0.123",
    "bidPrice": "45678.89",
    "bidQty": "1.234",
    "askPrice": "45678.91",
    "askQty": "0.567",
    "openPrice": "44444.34",
    "highPrice": "46000.00",
    "lowPrice": "44000.00",
    "volume": "1234.56",
    "quoteVolume": "56789012.34",
    "openTime": 1642233600000,
    "closeTime": 1642319999999,
    "firstId": 123456789,
    "lastId": 123456999,
    "count": 210
  },
  "tickerPrice": {
    "symbol": "BTCUSDT",
    "price": "45678.90"
  },
  "orderBook": {
    "lastUpdateId": 123456789,
    "bids": [
      ["45678.89", "1.234"],
      ["45678.88", "2.345"]
    ],
    "asks": [
      ["45678.91", "0.567"],
      ["45678.92", "1.234"]
    ]
  }
}
```

#### 2. Lambda Function (`binance-crawler`)
- **Runtime**: Node.js 18.x
- **Timeout**: 300 segundos
- **Memory**: 512 MB
- **Handler**: `index.handler`

**Variáveis de Ambiente:**
- `DYNAMODB_TABLE`: Nome da tabela DynamoDB
- `AWS_REGION`: Região AWS

#### 3. IAM Role e Policies
**Role**: `binance-crawler-lambda-role`

**Policies:**
- **CloudWatch Logs**: Criar e escrever logs
- **DynamoDB**: PutItem, GetItem, Query, Scan

#### 4. EventBridge Rule
- **Schedule**: `rate(1 hour)`
- **Target**: Lambda function
- **Description**: Executa o crawler a cada hora

### 🔄 Fluxo de Execução

#### 1. Inicialização
```javascript
// Configuração AWS
AWS.config.update({ region: process.env.AWS_REGION });
const dynamodb = new AWS.DynamoDB.DocumentClient();
```

#### 2. Obtenção de Símbolos
```javascript
// Requisição para API da Binance
const exchangeInfo = await makeRequest('https://api.binance.com/api/v3/exchangeInfo');
const symbols = exchangeInfo.symbols.filter(s => s.status === 'TRADING');
```

#### 3. Processamento em Lotes
```javascript
// Processamento em lotes de 5 símbolos
for (let i = 0; i < symbols.length; i += batchSize) {
  const batch = symbols.slice(i, i + batchSize);
  // Processar lote
  await new Promise(resolve => setTimeout(resolve, 1000)); // Delay
}
```

#### 4. Coleta de Dados por Símbolo
```javascript
// Requisições paralelas para cada símbolo
const [ticker24hr, tickerPrice, orderBook] = await Promise.all([
  makeRequest(`/ticker/24hr?symbol=${symbol}`),
  makeRequest(`/ticker/price?symbol=${symbol}`),
  makeRequest(`/depth?symbol=${symbol}&limit=10`)
]);
```

#### 5. Armazenamento no S3
```javascript
const timestamp = new Date();
const dateStr = timestamp.toISOString().split('T')[0];
const timeStr = timestamp.toISOString().replace(/[:.]/g, '-');
const key = `data/${dateStr}/${data.symbol}/${timeStr}.json`;

const params = {
  Bucket: bucketName,
  Key: key,
  Body: JSON.stringify(data, null, 2),
  ContentType: 'application/json',
  Metadata: {
    symbol: data.symbol,
    timestamp: data.timestamp,
    collected_at: timestamp.toISOString()
  }
};
await s3.putObject(params).promise();
```

## 🔧 Configurações de Performance

### Rate Limiting
- **Requests por segundo**: 10
- **Delay entre lotes**: 1000ms
- **Batch size**: 5 símbolos

### Timeouts
- **Lambda timeout**: 300 segundos
- **Request timeout**: 5000ms
- **Retry attempts**: 3

### Memória e CPU
- **Lambda memory**: 512 MB
- **Concurrent executions**: Ilimitado (configurável)

## 📊 Monitoramento e Logs

### CloudWatch Logs
**Log Group**: `/aws/lambda/binance-crawler`

**Logs Importantes:**
```
INFO: Iniciando crawler da Binance...
INFO: Total de símbolos encontrados: 1500
INFO: Símbolos ativos: 1200
INFO: Processando lote 1/240
INFO: Dados salvos para BTCUSDT
INFO: Processamento concluído: - Sucessos: 1200 - Falhas: 0
```

### Métricas Sugeridas
- **Invocation count**: Número de execuções
- **Duration**: Tempo de execução
- **Error rate**: Taxa de erro
- **Throttles**: Limitações de rate

## 🔒 Segurança

### IAM Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
          {
        "Effect": "Allow",
        "Action": [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ],
        "Resource": [
          "arn:aws:s3:::binance-crawler-data-*",
          "arn:aws:s3:::binance-crawler-data-*/*"
        ]
      }
  ]
}
```

### Rate Limiting da API
- Respeita limites da API da Binance
- Implementa delays entre requisições
- Tratamento de erros de rate limit

## 🚨 Tratamento de Erros

### Tipos de Erro
1. **Rate Limit Exceeded**
   - Implementa retry com backoff exponencial
   - Logs detalhados para debugging

2. **Network Errors**
   - Retry automático
   - Timeout configurável

3. **S3 Errors**
   - Retry com exponential backoff
   - Fallback para logging

### Estratégias de Retry
```javascript
async function makeRequestWithRetry(url, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await makeRequest(url);
    } catch (error) {
      if (attempt === maxRetries) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }
}
```

## 📈 Escalabilidade

### Horizontal Scaling
- **Lambda**: Escala automaticamente
- **S3**: Escalabilidade ilimitada
- **EventBridge**: Sem limitações de throughput

### Vertical Scaling
- **Memory**: Configurável (128MB - 3008MB)
- **Timeout**: Configurável (3s - 900s)
- **Batch Size**: Ajustável conforme necessidade

## 🔄 Manutenção

### Atualizações
1. **Código**: Deploy via Terraform
2. **Configurações**: Variáveis de ambiente
3. **Infraestrutura**: Terraform apply

### Backup e Recovery
- **S3**: Versionamento habilitado
- **Logs**: Retenção de 14 dias
- **Terraform State**: Versionado no S3

### Troubleshooting
1. **Verificar logs**: CloudWatch Logs
2. **Testar Lambda**: Invoke manual
3. **Verificar S3**: Console AWS
4. **Monitorar EventBridge**: CloudWatch Events

## 📋 Checklist de Deploy

### Pré-requisitos
- [ ] AWS CLI configurado
- [ ] Terraform instalado
- [ ] Node.js instalado
- [ ] Permissões AWS adequadas

### Deploy
- [ ] Executar `terraform init`
- [ ] Executar `terraform plan`
- [ ] Executar `terraform apply`
- [ ] Verificar logs do Lambda
- [ ] Testar execução manual

### Pós-deploy
- [ ] Configurar alertas CloudWatch
- [ ] Monitorar primeiras execuções
- [ ] Ajustar configurações se necessário
- [ ] Documentar customizações

## 🔮 Melhorias Futuras

### Funcionalidades Sugeridas
1. **Alertas**: Notificações para falhas
2. **Dashboard**: Visualização de dados
3. **Análise**: Machine Learning para previsões
4. **APIs**: REST API para consulta de dados
5. **Cache**: Redis para dados frequentes

### Otimizações
1. **Paralelização**: Mais requisições simultâneas
2. **Streaming**: Kinesis para processamento real-time
3. **Compressão**: Reduzir tamanho dos dados
4. **Índices**: Otimizar consultas DynamoDB

---

**Versão**: 1.0.0  
**Última atualização**: Janeiro 2024  
**Autor**: Tech Challenge Team 