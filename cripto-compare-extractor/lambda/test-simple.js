const https = require('https');

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
          reject(new Error(`Erro ao fazer parse do JSON: ${error.message}`));
        }
      });
    }).on('error', (error) => {
      console.error(`❌ Erro na requisição:`, error);
      reject(new Error(`Erro na requisição: ${error.message}`));
    });
  });
}

// Função para obter informações de todos os símbolos
async function getAllSymbols() {
  try {
    console.log('🔍 Obtendo lista de todos os símbolos...');
    const exchangeInfo = await makeRequest('https://api.binance.com/api/v3/exchangeInfo');
    
    console.log(`📊 Resposta da API:`);
    console.log(`- Tempo do servidor: ${exchangeInfo.serverTime}`);
    console.log(`- Símbolos encontrados: ${exchangeInfo.symbols ? exchangeInfo.symbols.length : 'N/A'}`);
    
    return exchangeInfo.symbols || [];
  } catch (error) {
    console.error('❌ Erro ao obter símbolos:', error);
    throw error;
  }
}

// Função principal do Lambda
exports.handler = async (event, context) => {
  console.log('🚀 Iniciando crawler da Binance (versão simplificada)...');
  
  try {
    // Obter todos os símbolos
    const symbols = await getAllSymbols();
    console.log(`📈 Total de símbolos encontrados: ${symbols.length}`);
    
    // Filtrar apenas símbolos ativos
    const activeSymbols = symbols.filter(symbol => symbol.status === 'TRADING');
    console.log(`📊 Símbolos ativos: ${activeSymbols.length}`);
    
    if (activeSymbols.length > 0) {
      console.log(`📋 Primeiros 5 símbolos ativos:`);
      activeSymbols.slice(0, 5).forEach((symbol, index) => {
        console.log(`  ${index + 1}. ${symbol.symbol} (${symbol.status})`);
      });
    }
    
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Crawler executado com sucesso',
        totalSymbols: symbols.length,
        activeSymbols: activeSymbols.length,
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