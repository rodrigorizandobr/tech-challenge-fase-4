const https = require('https');

// Função para fazer requisições HTTPS (igual ao Lambda)
function makeRequest(url) {
  return new Promise((resolve, reject) => {
    console.log(`🌐 Fazendo requisição para: ${url}`);
    
    https.get(url, (res) => {
      let data = '';
      
      console.log(`📡 Status: ${res.statusCode}`);
      console.log(`📡 Headers:`, res.headers);
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          console.log(`📄 Dados recebidos (${data.length} bytes):`);
          console.log(data.substring(0, 500) + (data.length > 500 ? '...' : ''));
          
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
    
    if (exchangeInfo.symbols && exchangeInfo.symbols.length > 0) {
      console.log(`📋 Primeiros 5 símbolos:`);
      exchangeInfo.symbols.slice(0, 5).forEach((symbol, index) => {
        console.log(`  ${index + 1}. ${symbol.symbol} (${symbol.status})`);
      });
    }
    
    return exchangeInfo.symbols || [];
  } catch (error) {
    console.error('❌ Erro ao obter símbolos:', error);
    throw error;
  }
}

// Função para testar um símbolo específico
async function testSymbol(symbol) {
  try {
    console.log(`\n🧪 Testando símbolo: ${symbol}`);
    
    const [ticker24hr, tickerPrice, orderBook] = await Promise.all([
      makeRequest(`https://api.binance.com/api/v3/ticker/24hr?symbol=${symbol}`),
      makeRequest(`https://api.binance.com/api/v3/ticker/price?symbol=${symbol}`),
      makeRequest(`https://api.binance.com/api/v3/depth?symbol=${symbol}&limit=5`)
    ]);

    console.log(`✅ Dados obtidos para ${symbol}:`);
    console.log(`- Ticker 24h: ${ticker24hr.symbol} - Preço: ${ticker24hr.lastPrice}`);
    console.log(`- Ticker Price: ${tickerPrice.price}`);
    console.log(`- Order Book: ${orderBook.bids.length} bids, ${orderBook.asks.length} asks`);
    
    return {
      symbol: symbol,
      ticker24hr: ticker24hr,
      tickerPrice: tickerPrice,
      orderBook: orderBook,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    console.error(`❌ Erro ao testar símbolo ${symbol}:`, error);
    return null;
  }
}

// Função principal de teste
async function testCrawler() {
  console.log('🚀 Iniciando teste local do crawler da Binance...\n');
  
  try {
    // 1. Testar obtenção de símbolos
    console.log('=' * 50);
    console.log('1. TESTANDO OBTENÇÃO DE SÍMBOLOS');
    console.log('=' * 50);
    
    const symbols = await getAllSymbols();
    console.log(`\n📈 Total de símbolos encontrados: ${symbols.length}`);
    
    if (symbols.length === 0) {
      console.log('❌ Nenhum símbolo encontrado! Verificando possíveis problemas...');
      
      // Testar se a API está acessível
      console.log('\n🔍 Testando conectividade com a API...');
      try {
        const testResponse = await makeRequest('https://api.binance.com/api/v3/ping');
        console.log('✅ API está acessível:', testResponse);
      } catch (error) {
        console.error('❌ API não está acessível:', error.message);
      }
      
      return;
    }
    
    // 2. Filtrar símbolos ativos
    console.log('\n' + '=' * 50);
    console.log('2. FILTRANDO SÍMBOLOS ATIVOS');
    console.log('=' * 50);
    
    const activeSymbols = symbols.filter(symbol => symbol.status === 'TRADING');
    console.log(`📊 Símbolos ativos: ${activeSymbols.length}`);
    
    if (activeSymbols.length === 0) {
      console.log('❌ Nenhum símbolo ativo encontrado!');
      console.log('📋 Status dos símbolos:');
      const statusCount = {};
      symbols.forEach(symbol => {
        statusCount[symbol.status] = (statusCount[symbol.status] || 0) + 1;
      });
      Object.entries(statusCount).forEach(([status, count]) => {
        console.log(`  - ${status}: ${count}`);
      });
      return;
    }
    
    // 3. Testar alguns símbolos específicos
    console.log('\n' + '=' * 50);
    console.log('3. TESTANDO SÍMBOLOS ESPECÍFICOS');
    console.log('=' * 50);
    
    const testSymbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'];
    const results = [];
    
    for (const symbol of testSymbols) {
      const result = await testSymbol(symbol);
      if (result) {
        results.push(result);
      }
    }
    
    console.log(`\n✅ Teste concluído! ${results.length} símbolos testados com sucesso.`);
    
    // 4. Simular salvamento no S3
    console.log('\n' + '=' * 50);
    console.log('4. SIMULANDO SALVAMENTO NO S3');
    console.log('=' * 50);
    
    for (const result of results) {
      const timestamp = new Date();
      const dateStr = timestamp.toISOString().split('T')[0];
      const timeStr = timestamp.toISOString().replace(/[:.]/g, '-');
      const key = `data/${dateStr}/${result.symbol}/${timeStr}.json`;
      
      console.log(`💾 Simulando salvamento: ${key}`);
      console.log(`   - Tamanho dos dados: ${JSON.stringify(result).length} bytes`);
      console.log(`   - Preço atual: ${result.tickerPrice.price}`);
    }
    
  } catch (error) {
    console.error('❌ Erro no teste:', error);
  }
}

// Executar o teste
testCrawler().catch(console.error); 