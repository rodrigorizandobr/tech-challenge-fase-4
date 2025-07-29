const AWS = require('aws-sdk');
const https = require('https');

// Configurar AWS
AWS.config.update({ region: process.env.AWS_REGION || 'us-east-1' });
const s3 = new AWS.S3();
const bucketName = process.env.S3_BUCKET;

// Função para fazer requisições HTTPS
function makeRequest(url) {
  return new Promise((resolve, reject) => {
    console.log(`🌐 Fazendo requisição para: ${url}`);
    
    https.get(url, (res) => {
      let data = '';
      
      console.log(`📡 Status: ${res.statusCode}`);
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          console.log(`📄 Dados recebidos (${data.length} bytes)`);
          const jsonData = JSON.parse(data);
          resolve(jsonData);
        } catch (error) {
          console.error(`❌ Erro ao fazer parse do JSON:`, error);
          console.error(`📄 Primeiros 200 caracteres da resposta:`, data.substring(0, 200));
          reject(new Error(`Erro ao fazer parse do JSON: ${error.message}`));
        }
      });
    }).on('error', (error) => {
      console.error(`❌ Erro na requisição:`, error);
      reject(new Error(`Erro na requisição: ${error.message}`));
    });
  });
}

// Função para obter lista de criptomoedas do CryptoCompare
async function getCryptoList() {
  try {
    console.log('🔍 Obtendo lista de criptomoedas do CryptoCompare...');
    const response = await makeRequest('https://min-api.cryptocompare.com/data/top/mktcapfull?limit=100&tsym=USD');
    return response.Data || [];
  } catch (error) {
    console.error('❌ Erro ao obter lista de criptomoedas:', error);
    throw error;
  }
}

// Função para converter timestamp Unix para formato de data legível YYYY-MM-DD HH:MM:SS
function formatDate(timestamp) {
  const date = new Date(timestamp * 1000);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

// Função para obter informações detalhadas de uma criptomoeda
async function getCryptoInfo(symbol) {
  try {
    // Obter dados históricos dos últimos 5 anos (1825 dias)
    const histoData = await makeRequest(`https://min-api.cryptocompare.com/data/v2/histoday?fsym=${symbol}&tsym=USD&limit=1825`);
    
    // Processar dados históricos para CSV
    const csvRows = [];
    if (histoData.Data?.Data) {
      histoData.Data.Data.forEach(day => {
        csvRows.push({
          symbol: symbol,
          date: formatDate(day.time),
          timestamp: day.time,
          high: day.high,
          low: day.low,
          open: day.open,
          close: day.close,
          volumefrom: day.volumefrom,
          volumeto: day.volumeto
        });
      });
    }

    return {
      symbol: symbol,
      csv_rows: csvRows,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    console.error(`❌ Erro ao obter informações da criptomoeda ${symbol}:`, error);
    return null;
  }
}

// Função para salvar dados no S3 em formato CSV
async function saveToS3(csvData, dateStr) {
  try {
    // Criar cabeçalho CSV
    const header = 'symbol|datetime|timestamp|high|low|open|close|volumefrom|volumeto\n';

    // Converter dados para linhas CSV
    const csvRows = csvData.map(row => 
      `${row.symbol}|${row.date}|${row.timestamp}|${row.high}|${row.low}|${row.open}|${row.close}|${row.volumefrom}|${row.volumeto}`
    ).join('\n');

    const csvContent = header + csvRows;

    // Salvar na raiz do bucket como raw.csv
    const key = 'raw.csv';

    const params = {
      Bucket: bucketName,
      Key: key,
      Body: csvContent,
      ContentType: 'text/csv',
      Metadata: {
        date: dateStr,
        total_records: csvData.length.toString(),
        collected_at: new Date().toISOString()
      }
    };

    await s3.putObject(params).promise();
    console.log(`💾 Dados salvos no S3: ${key} (${csvData.length} registros)`);
  } catch (error) {
    console.error(`❌ Erro ao salvar dados no S3:`, error);
    throw error;
  }
}

// Função para processar criptomoedas em lotes
async function processCryptoBatch(cryptoList, batchSize = 5) {
  const allCsvData = [];
  const results = [];
  
  for (let i = 0; i < cryptoList.length; i += batchSize) {
    const batch = cryptoList.slice(i, i + batchSize);
    console.log(`📊 Processando lote ${Math.floor(i / batchSize) + 1}/${Math.ceil(cryptoList.length / batchSize)}`);
    
    const batchPromises = batch.map(async (crypto) => {
      const symbol = crypto.CoinInfo?.Name || crypto.symbol;
      const data = await getCryptoInfo(symbol);
      
      if (data && data.csv_rows.length > 0) {
        allCsvData.push(...data.csv_rows);
        return { symbol: symbol, status: 'success', records: data.csv_rows.length };
      } else {
        return { symbol: symbol, status: 'error', records: 0 };
      }
    });

    const batchResults = await Promise.allSettled(batchPromises);
    results.push(...batchResults);
    
    // Aguardar um pouco entre os lotes para não sobrecarregar a API
    if (i + batchSize < cryptoList.length) {
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  return { results, csvData: allCsvData };
}

// Função principal do Lambda
exports.handler = async (event, context) => {
  console.log('🚀 Iniciando crawler de criptomoedas...');
  
  try {
    // Obter lista de criptomoedas
    const cryptoList = await getCryptoList();
    console.log(`📈 Total de criptomoedas encontradas: ${cryptoList.length}`);
    
    if (cryptoList.length === 0) {
      throw new Error('Nenhuma criptomoeda encontrada');
    }
    
    // Mostrar as top 10 criptomoedas
    console.log('🏆 Top 10 criptomoedas por market cap:');
    cryptoList.slice(0, 10).forEach((crypto, index) => {
      const name = crypto.CoinInfo?.FullName || crypto.CoinInfo?.Name || 'Unknown';
      const symbol = crypto.CoinInfo?.Name || 'Unknown';
      console.log(`  ${index + 1}. ${name} (${symbol})`);
    });
    
    // Processar criptomoedas em lotes
    const { results, csvData } = await processCryptoBatch(cryptoList, 5);
    
    // Salvar dados em CSV
    const dateStr = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    await saveToS3(csvData, dateStr);
    
    // Contar resultados
    const successful = results.filter(r => r.status === 'fulfilled' && r.value.status === 'success').length;
    const failed = results.length - successful;
    const totalRecords = csvData.length;
    
    console.log(`✅ Processamento concluído:`);
    console.log(`- Sucessos: ${successful}`);
    console.log(`- Falhas: ${failed}`);
    console.log(`- Total de registros CSV: ${totalRecords}`);
    
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Crawler de criptomoedas executado com sucesso',
        totalCryptos: cryptoList.length,
        successful,
        failed,
        totalRecords,
        csvFile: 'raw.csv',
        topCryptos: cryptoList.slice(0, 5).map(c => ({
          name: c.CoinInfo?.FullName || c.CoinInfo?.Name || 'Unknown',
          symbol: c.CoinInfo?.Name || 'Unknown'
        })),
        timestamp: new Date().toISOString()
      })
    };
    
  } catch (error) {
    console.error('❌ Erro no crawler:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Erro no crawler',
        error: error.message,
        timestamp: new Date().toISOString()
      })
    };
  }
}; 