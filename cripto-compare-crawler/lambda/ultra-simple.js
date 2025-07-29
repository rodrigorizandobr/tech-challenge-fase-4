const https = require('https');

// Função principal do Lambda
exports.handler = async (event, context) => {
  console.log('🚀 Iniciando teste ultra-simples...');
  
  try {
    console.log('🔍 Testando conectividade com a API...');
    
    // Teste simples de conectividade
    const testUrl = 'https://api.binance.com/api/v3/ping';
    
    const result = await new Promise((resolve, reject) => {
      https.get(testUrl, (res) => {
        let data = '';
        
        console.log(`📡 Status: ${res.statusCode}`);
        console.log(`📡 Headers:`, res.headers);
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          try {
            console.log(`📄 Dados recebidos: ${data}`);
            const jsonData = JSON.parse(data);
            resolve(jsonData);
          } catch (error) {
            console.error(`❌ Erro ao fazer parse:`, error);
            reject(error);
          }
        });
      }).on('error', (error) => {
        console.error(`❌ Erro na requisição:`, error);
        reject(error);
      });
    });
    
    console.log('✅ Teste de conectividade bem-sucedido:', result);
    
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Teste de conectividade bem-sucedido',
        pingResult: result,
        timestamp: new Date().toISOString()
      })
    };
    
  } catch (error) {
    console.error('❌ Erro no teste:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Erro no teste',
        error: error.message,
        timestamp: new Date().toISOString()
      })
    };
  }
}; 