const AWS = require('aws-sdk');

// Configurar AWS
AWS.config.update({ region: 'us-east-1' });
const s3 = new AWS.S3();
const bucketName = 'binance-crawler-data'; // Substitua pelo nome do seu bucket

// Função para obter dados de um símbolo específico
async function getSymbolData(symbol, limit = 10) {
  try {
    // Listar objetos no S3 para o símbolo específico
    const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    const prefix = `data/${today}/${symbol}/`;
    
    const listParams = {
      Bucket: bucketName,
      Prefix: prefix,
      MaxKeys: limit
    };

    const listResult = await s3.listObjectsV2(listParams).promise();
    
    if (!listResult.Contents || listResult.Contents.length === 0) {
      console.log(`Nenhum dado encontrado para ${symbol} hoje`);
      return [];
    }

    // Obter os dados dos objetos
    const dataPromises = listResult.Contents
      .sort((a, b) => b.LastModified - a.LastModified) // Mais recente primeiro
      .slice(0, limit)
      .map(async (object) => {
        const getParams = {
          Bucket: bucketName,
          Key: object.Key
        };
        
        const result = await s3.getObject(getParams).promise();
        return JSON.parse(result.Body.toString());
      });

    return await Promise.all(dataPromises);
  } catch (error) {
    console.error(`Erro ao buscar dados para ${symbol}:`, error);
    return [];
  }
}

// Função para analisar variação de preço
function analyzePriceChange(data) {
  if (data.length < 2) return null;

  const latest = data[0];
  const previous = data[1];

  const currentPrice = parseFloat(latest.tickerPrice.price);
  const previousPrice = parseFloat(previous.tickerPrice.price);
  const change = currentPrice - previousPrice;
  const changePercent = (change / previousPrice) * 100;

  return {
    symbol: latest.symbol,
    currentPrice,
    previousPrice,
    change,
    changePercent,
    timestamp: latest.timestamp
  };
}

// Função para obter top movers (maior variação)
async function getTopMovers(limit = 10) {
  try {
    // Listar todos os símbolos disponíveis hoje
    const today = new Date().toISOString().split('T')[0];
    const prefix = `data/${today}/`;
    
    const listParams = {
      Bucket: bucketName,
      Prefix: prefix,
      Delimiter: '/'
    };

    const listResult = await s3.listObjectsV2(listParams).promise();
    
    if (!listResult.CommonPrefixes) {
      console.log('Nenhum símbolo encontrado hoje');
      return [];
    }

    // Extrair símbolos únicos
    const uniqueSymbols = listResult.CommonPrefixes
      .map(prefix => prefix.Prefix.split('/')[2]) // data/YYYY-MM-DD/SYMBOL/
      .filter(symbol => symbol);

    const topMovers = [];

    // Analisar cada símbolo
    for (const symbol of uniqueSymbols.slice(0, 50)) { // Limitar para performance
      const data = await getSymbolData(symbol, 2);
      const analysis = analyzePriceChange(data);
      
      if (analysis) {
        topMovers.push(analysis);
      }
    }

    // Ordenar por variação percentual
    return topMovers
      .sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent))
      .slice(0, limit);
  } catch (error) {
    console.error('Erro ao obter top movers:', error);
    return [];
  }
}

// Função para obter estatísticas gerais
async function getGeneralStats() {
  try {
    const today = new Date().toISOString().split('T')[0];
    const prefix = `data/${today}/`;
    
    const listParams = {
      Bucket: bucketName,
      Prefix: prefix
    };

    const listResult = await s3.listObjectsV2(listParams).promise();
    
    return {
      totalRecords: listResult.Contents ? listResult.Contents.length : 0,
      timestamp: new Date().toISOString(),
      date: today
    };
  } catch (error) {
    console.error('Erro ao obter estatísticas:', error);
    return null;
  }
}

// Função para obter volume de negociação
async function getTradingVolume(symbol) {
  try {
    const data = await getSymbolData(symbol, 1);
    
    if (data.length > 0) {
      const ticker = data[0].ticker24hr;
      return {
        symbol,
        volume: parseFloat(ticker.volume),
        quoteVolume: parseFloat(ticker.quoteVolume),
        count: parseInt(ticker.count),
        timestamp: data[0].timestamp
      };
    }
    
    return null;
  } catch (error) {
    console.error(`Erro ao obter volume para ${symbol}:`, error);
    return null;
  }
}

// Função principal de exemplo
async function main() {
  console.log('📊 Análise de Dados da Binance');
  console.log('================================');

  // 1. Estatísticas gerais
  console.log('\n1. Estatísticas Gerais:');
  const stats = await getGeneralStats();
  if (stats) {
    console.log(`Total de registros: ${stats.totalRecords}`);
    console.log(`Timestamp: ${stats.timestamp}`);
  }

  // 2. Análise do BTCUSDT
  console.log('\n2. Análise do BTCUSDT:');
  const btcData = await getSymbolData('BTCUSDT', 5);
  if (btcData.length > 0) {
    const analysis = analyzePriceChange(btcData);
    if (analysis) {
      console.log(`Preço atual: $${analysis.currentPrice.toFixed(2)}`);
      console.log(`Variação: ${analysis.change.toFixed(2)} (${analysis.changePercent.toFixed(2)}%)`);
    }

    const volume = await getTradingVolume('BTCUSDT');
    if (volume) {
      console.log(`Volume 24h: ${volume.volume.toFixed(2)} BTC`);
      console.log(`Volume em USD: $${volume.quoteVolume.toFixed(2)}`);
    }
  }

  // 3. Top movers
  console.log('\n3. Top 5 Movers (Maior Variação):');
  const topMovers = await getTopMovers(5);
  topMovers.forEach((mover, index) => {
    const direction = mover.changePercent > 0 ? '📈' : '📉';
    console.log(`${index + 1}. ${mover.symbol}: ${direction} ${mover.changePercent.toFixed(2)}%`);
  });

  // 4. Análise de outros pares populares
  console.log('\n4. Análise de Pares Populares:');
  const popularPairs = ['ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT'];
  
  for (const pair of popularPairs) {
    const data = await getSymbolData(pair, 2);
    const analysis = analyzePriceChange(data);
    
    if (analysis) {
      const direction = analysis.changePercent > 0 ? '📈' : '📉';
      console.log(`${pair}: ${direction} ${analysis.changePercent.toFixed(2)}%`);
    }
  }
}

// Executar se chamado diretamente
if (require.main === module) {
  main().catch(console.error);
}

module.exports = {
  getSymbolData,
  analyzePriceChange,
  getTopMovers,
  getGeneralStats,
  getTradingVolume
}; 