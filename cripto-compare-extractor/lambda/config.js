module.exports = {
  // Configurações da API da Binance
  binance: {
    baseUrl: 'https://api.binance.com/api/v3',
    endpoints: {
      exchangeInfo: '/exchangeInfo',
      ticker24hr: '/ticker/24hr',
      tickerPrice: '/ticker/price',
      orderBook: '/depth'
    },
    rateLimit: {
      requestsPerSecond: 10,
      delayBetweenBatches: 1000 // ms
    }
  },

  // Configurações do processamento
  processing: {
    batchSize: 5, // Número de símbolos por lote
    maxRetries: 3,
    retryDelay: 1000, // ms
    timeout: 5000 // ms por requisição
  },

  // Configurações do S3
  s3: {
    bucketName: process.env.S3_BUCKET || 'binance-crawler-data',
    region: process.env.AWS_REGION || 'us-east-1'
  },

  // Configurações de logging
  logging: {
    level: 'info',
    enableDetailedLogs: true
  },

  // Configurações de monitoramento
  monitoring: {
    enableMetrics: true,
    logSuccessRate: true,
    logProcessingTime: true
  }
}; 