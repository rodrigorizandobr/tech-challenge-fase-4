// Teste simples para verificar as correções do CSV
const https = require('https');

// Função para fazer requisições HTTP
function makeRequest(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (error) {
          reject(error);
        }
      });
    }).on('error', reject);
  });
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
    console.log(`🔍 Testando ${symbol}...`);
    
    // Obter dados históricos dos últimos 30 dias
    const histoData = await makeRequest(`https://min-api.cryptocompare.com/data/v2/histoday?fsym=${symbol}&tsym=USD&limit=30`);
    
    // Processar dados históricos para CSV
    const csvRows = [];
    if (histoData.Data?.Data) {
      console.log(`📊 Encontrados ${histoData.Data.Data.length} dias de dados para ${symbol}`);
      
      histoData.Data.Data.forEach((day, index) => {
        const formattedDate = formatDate(day.time);
        csvRows.push({
          symbol: symbol,
          date: formattedDate,
          timestamp: day.time,
          high: day.high,
          low: day.low,
          open: day.open,
          close: day.close,
          volumefrom: day.volumefrom,
          volumeto: day.volumeto
        });
        
        // Mostrar os primeiros 3 dias como exemplo
        if (index < 3) {
          console.log(`  ${formattedDate} (${day.time}): High=${day.high}, Low=${day.low}, Open=${day.open}, Close=${day.close}`);
        }
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

// Teste principal
async function testCsvCorrections() {
  console.log('🧪 Testando correções do CSV com novo formato de data...\n');
  
  // Testar com algumas criptomoedas
  const testSymbols = ['BTC', 'ETH', 'ADA'];
  
  for (const symbol of testSymbols) {
    const result = await getCryptoInfo(symbol);
    if (result) {
      console.log(`✅ ${symbol}: ${result.csv_rows.length} registros CSV\n`);
    } else {
      console.log(`❌ ${symbol}: Falha\n`);
    }
  }
  
  console.log('🎯 Teste concluído!');
}

// Executar teste
testCsvCorrections().catch(console.error); 