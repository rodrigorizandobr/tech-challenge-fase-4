# Mock do Heterium (HET) - Documentação

## 🎭 Visão Geral

O mock do **Heterium (HET)** foi implementado para permitir testes e demonstrações da API mesmo sem dados reais no S3. Ele gera dados simulados realistas para a criptomoeda Heterium.

## 🔧 Implementação

### Localização do Código

O mock está implementado no arquivo `api/app/models.py`:

```python
def _create_het_mock_data(self) -> pd.DataFrame:
    """Cria dados mock para Heterium (HET)"""
```

### Ativação Automática

O mock é ativado automaticamente quando o símbolo `HET` é solicitado:

```python
# Mock temporário para Heterium (HET)
if symbol.upper() == "HET":
    logger.info("🎭 Usando dados mock para Heterium (HET)")
    return self._create_het_mock_data()
```

## 📊 Características dos Dados Mock

### Período de Dados
- **Duração**: 30 dias de dados históricos
- **Frequência**: Dados diários
- **Período**: Últimos 30 dias até a data atual

### Parâmetros de Simulação
- **Preço base**: $150 USD
- **Volatilidade**: 15%
- **Seed aleatório**: 42 (para reprodutibilidade)
- **Market cap**: 10M tokens em circulação

### Indicadores Técnicos Incluídos

#### Preços e Volumes
- `fechamento`, `abertura`, `maximo`, `minimo`
- `volume`, `market_cap`
- `price_change_24h`, `volume_change_24h`

#### Médias Móveis
- `sma_20` (Simple Moving Average 20 períodos)
- `hull_moving_average`
- `kaufman_adaptive_moving_average`

#### Osciladores
- `rsi` (Relative Strength Index)
- `macd` (Moving Average Convergence Divergence)
- `stochastic_k`, `stochastic_d`
- `williams_r` (Williams %R)
- `cci` (Commodity Channel Index)
- `mfi` (Money Flow Index)

#### Bandas e Canais
- `bollinger_upper`, `bollinger_lower`
- `support_level`, `resistance_level`
- `donchian_channel_high`, `donchian_channel_low`
- `keltner_channel_high`, `keltner_channel_low`

#### Indicadores de Tendência
- `adx` (Average Directional Index)
- `trend_strength`
- `momentum`
- `price_momentum`, `volume_momentum`

#### Indicadores de Williams
- `williams_alligator_blue`, `williams_alligator_red`, `williams_alligator_green`
- `fractal_high`, `fractal_low`
- `gator_jaw`, `gator_teeth`, `gator_lips`

#### Outros Indicadores
- `atr` (Average True Range)
- `obv` (On Balance Volume)
- `roc` (Rate of Change)
- `awesome_oscillator`
- `accelerator_oscillator`
- `force_index`
- `ease_of_movement`

## 🧪 Como Testar

### 1. Teste Rápido (Bash)
```bash
cd api
./test-het-quick.sh
```

### 2. Teste Completo (Python)
```bash
cd api
python test_het_mock.py http://localhost:8000
```

### 3. Teste Manual (cURL)
```bash
curl http://localhost:8000/symbol/HET
```

### 4. Comparação com Outros Símbolos
```bash
curl http://localhost:8000/symbol/BTC
curl http://localhost:8000/symbol/ETH
curl http://localhost:8000/symbol/HET
```

## 📈 Exemplo de Resposta

```json
{
  "ativo": "HET",
  "timestamp": "2025-01-27T10:30:00.123456",
  "modelos": {
    "regressor_gbr": {
      "predicao": 152.45,
      "modelo": "regressor_gbr",
      "tipo": "regressor",
      "versao": "20250729-2130"
    },
    "regressor_lin": {
      "predicao": 148.32,
      "modelo": "regressor_lin",
      "tipo": "regressor",
      "versao": "20250729-2130"
    },
    "classifier_log": {
      "predicao": 1,
      "probabilidade": 0.75,
      "modelo": "classifier_log",
      "tipo": "classifier",
      "versao": "20250729-2130"
    }
  },
  "total_modelos": 3,
  "dados_utilizados": "Últimos 30 registros",
  "features_utilizadas": 84
}
```

## 🔍 Logs Detalhados

Quando o mock é usado, você verá logs como:

```
🎭 Usando dados mock para Heterium (HET)
🎭 Criando dados mock para Heterium...
✅ Dados mock criados para HET: 30 registros, 85 colunas
🔧 Preparando features de 30 registros...
📊 Colunas disponíveis: 85
🔍 Features selecionadas: 84
📈 Features numéricas: 84 colunas
✅ Features preparadas: 84 colunas
🔮 Fazendo predição com regressor_gbr (tipo: regressor)
✅ Predição regressora: 152.45
🔮 Fazendo predição com classifier_log (tipo: classifier)
✅ Predição classificadora: 1 (prob: 0.75)
🎉 Predições concluídas: 3/3 modelos
```

## 🎯 Vantagens do Mock

### 1. **Testes Independentes**
- Não depende de dados reais no S3
- Funciona mesmo sem conexão com AWS
- Dados consistentes e reprodutíveis

### 2. **Demonstração**
- Mostra como a API funciona
- Permite testes de todos os endpoints
- Valida o fluxo completo de predição

### 3. **Desenvolvimento**
- Facilita desenvolvimento e debug
- Permite testes rápidos
- Não consome recursos do S3

### 4. **Validação de Modelos**
- Testa se os modelos carregam corretamente
- Valida o processamento de features
- Verifica a lógica de predição

## 🔧 Configuração

### Parâmetros Ajustáveis

No método `_create_het_mock_data()`, você pode ajustar:

```python
# Dados base para Heterium
base_price = 150.0  # Preço base em USD
volatility = 0.15   # Volatilidade de 15%
```

### Adicionando Novos Indicadores

Para adicionar novos indicadores técnicos:

```python
data.append({
    # ... outros campos ...
    'novo_indicador': round(np.random.normal(0, 1), 4),
})
```

## 🚀 Próximos Passos

1. **Testar o mock**:
   ```bash
   cd api
   ./test-het-quick.sh
   ```

2. **Verificar logs**:
   - Os logs mostram o processo completo
   - Facilita debug e validação

3. **Comparar com dados reais**:
   - Quando dados reais estiverem disponíveis
   - Validar se o mock é realista

4. **Expandir para outros símbolos**:
   - Adicionar mocks para outras criptomoedas
   - Criar dados simulados mais complexos

## 📋 Resumo

O mock do Heterium é uma funcionalidade temporária que permite:

- ✅ **Testes independentes** da API
- ✅ **Demonstração** do funcionamento
- ✅ **Desenvolvimento** sem dependências externas
- ✅ **Validação** de modelos e features
- ✅ **Logs detalhados** para debug

O mock está ativo e funcionando! 🎉 