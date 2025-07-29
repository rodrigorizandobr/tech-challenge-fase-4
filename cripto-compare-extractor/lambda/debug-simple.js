const https = require('https');

// Função para fazer requisições HTTPS
function makeRequest(url) {
  return new Promise((resolve, reject) => {
    console.log(`🌐 Fazendo requisição para: ${url}`);
    
    const options = {
      hostname: 'api.binance.com',
      port: 443,
      path: '/api/v3/exchangeInfo',
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; BinanceCrawler/1.0)'
      }
    };
    
    const req = https.request(options, (res) => {
      let data = '';
      
      console.log(`📡 Status: ${res.statusCode}`);
      console.log(`📡 Headers:`, res.headers);
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          console.log(`📄 Dados recebidos (${data.length} bytes)`);
          console.log(`📄 Primeiros 200 caracteres:`, data.substring(0, 200));
          
          const jsonData = JSON.parse(data);
          resolve(jsonData);
        } catch (error) {
          console.error(`❌ Erro ao fazer parse do JSON:`, error);
          reject(new Error(`Erro ao fazer parse do JSON: ${error.message}`));
        }
      });
    });
    
    req.on('error', (error) => {
      console.error(`❌ Erro na requisição:`, error);
      reject(new Error(`Erro na requisição: ${error.message}`));
    });
    
    req.end();
  });
}

// Função principal do Lambda
exports.handler = async (event, context) => {
  console.log('🚀 Iniciando debug do crawler da Binance...');
  
  try {
    // Testar conectividade básica
    console.log('🔍 Testando conectividade com a API...');
    
    const exchangeInfo = await makeRequest('https://api.binance.com/api/v3/exchangeInfo');
    
    console.log(`📊 Resposta da API:`);
    console.log(`- Tempo do servidor: ${exchangeInfo.serverTime}`);
    console.log(`- Símbolos encontrados: ${exchangeInfo.symbols ? exchangeInfo.symbols.length : 'N/A'}`);
    
    if (exchangeInfo.symbols && exchangeInfo.symbols.length > 0) {
      console.log(`📋 Primeiros 3 símbolos:`);
      exchangeInfo.symbols.slice(0, 3).forEach((symbol, index) => {
        console.log(`  ${index + 1}. ${symbol.symbol} (${symbol.status})`);
      });
    }
    
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Debug executado com sucesso',
        totalSymbols: exchangeInfo.symbols ? exchangeInfo.symbols.length : 0,
        serverTime: exchangeInfo.serverTime,
        timestamp: new Date().toISOString()
      })
    };
    
  } catch (error) {
    console.error('❌ Erro no debug:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Erro no debug',
        error: error.message,
        timestamp: new Date().toISOString()
      })
    };
  }
}; 