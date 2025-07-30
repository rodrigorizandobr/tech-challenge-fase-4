import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PredictionEngine:
    def __init__(self, model_manager):
        self.model_manager = model_manager
        
    def get_latest_data_for_symbol(self, symbol: str) -> pd.DataFrame:
        """Obtém os dados mais recentes para um símbolo específico do S3"""
        try:
            import boto3
            s3_client = boto3.client("s3")
            bucket_name = "criptos-data"
            
            logger.info(f"🔍 Buscando dados para {symbol} no S3...")
            
            # Mock temporário para Heterium (HET)
            if symbol.upper() == "HET":
                logger.info("🎭 Usando dados mock para Heterium (HET)")
                return self._create_het_mock_data()
            
            # Lista arquivos de dados para o símbolo
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=f"data/{symbol}/",
                MaxKeys=100
            )
            
            if 'Contents' not in response:
                logger.warning(f"⚠️ Nenhum dado encontrado para {symbol}")
                return pd.DataFrame()
            
            # Pega o arquivo mais recente
            latest_file = None
            latest_date = None
            
            for obj in response['Contents']:
                if obj['Key'].endswith('.csv'):
                    # Extrai data do nome do arquivo (assumindo formato: symbol_YYYY-MM-DD.csv)
                    filename = obj['Key'].split('/')[-1]
                    logger.debug(f"Verificando arquivo: {filename}")
                    
                    if '_' in filename:
                        date_part = filename.split('_')[-1].replace('.csv', '')
                        try:
                            file_date = datetime.strptime(date_part, '%Y-%m-%d')
                            if latest_date is None or file_date > latest_date:
                                latest_date = file_date
                                latest_file = obj['Key']
                                logger.debug(f"Novo arquivo mais recente: {filename} ({file_date})")
                        except Exception as e:
                            logger.debug(f"Erro ao parsear data do arquivo {filename}: {e}")
                            continue
            
            if latest_file:
                logger.info(f"📥 Baixando arquivo mais recente: {latest_file}")
                # Download do arquivo mais recente
                local_path = f"/tmp/{symbol}_latest.csv"
                s3_client.download_file(bucket_name, latest_file, local_path)
                
                # Carrega os dados
                df = pd.read_csv(local_path)
                logger.info(f"✅ Dados carregados para {symbol}: {len(df)} registros, {len(df.columns)} colunas")
                
                # Remove arquivo local
                import os
                try:
                    os.remove(local_path)
                    logger.debug(f"Arquivo temporário removido: {local_path}")
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo temporário {local_path}: {e}")
                
                return df
            else:
                logger.warning(f"⚠️ Nenhum arquivo de dados válido encontrado para {symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados para {symbol}: {e}")
            return pd.DataFrame()
    
    def _create_het_mock_data(self) -> pd.DataFrame:
        """Cria dados mock para Heterium (HET)"""
        import numpy as np
        from datetime import datetime, timedelta
        
        logger.info("🎭 Criando dados mock para Heterium...")
        
        # Gera dados dos últimos 30 dias
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Dados base para Heterium
        base_price = 150.0  # Preço base em USD
        volatility = 0.15   # Volatilidade de 15%
        
        # Gera dados simulados
        np.random.seed(42)  # Para reprodutibilidade
        
        data = []
        current_price = base_price
        
        for i, date in enumerate(dates):
            # Simula movimento de preço
            price_change = np.random.normal(0, volatility)
            current_price = current_price * (1 + price_change)
            
            # Calcula outros indicadores
            volume = np.random.uniform(1000000, 5000000)
            market_cap = current_price * 10000000  # 10M tokens em circulação
            
            # Indicadores técnicos simulados
            sma_20 = current_price * (1 + np.random.normal(0, 0.05))
            rsi = np.random.uniform(30, 70)
            macd = np.random.normal(0, 0.1)
            
            # Features adicionais
            price_change_24h = np.random.normal(0, 0.1)
            volume_change_24h = np.random.normal(0, 0.2)
            
            data.append({
                'data': date.strftime('%Y-%m-%d'),
                'ativo': 'HET',
                'timestamp': date.isoformat(),
                'fechamento': round(current_price, 2),
                'abertura': round(current_price * (1 + np.random.normal(0, 0.02)), 2),
                'maximo': round(current_price * (1 + abs(np.random.normal(0, 0.03))), 2),
                'minimo': round(current_price * (1 - abs(np.random.normal(0, 0.03))), 2),
                'volume': round(volume, 0),
                'market_cap': round(market_cap, 0),
                'price_change_24h': round(price_change_24h, 4),
                'volume_change_24h': round(volume_change_24h, 4),
                'sma_20': round(sma_20, 2),
                'rsi': round(rsi, 2),
                'macd': round(macd, 4),
                'volatility': round(volatility * 100, 2),
                'price_momentum': round(np.random.normal(0, 0.1), 4),
                'volume_momentum': round(np.random.normal(0, 0.2), 4),
                'trend_strength': round(np.random.uniform(0, 1), 4),
                'support_level': round(current_price * 0.9, 2),
                'resistance_level': round(current_price * 1.1, 2),
                'bollinger_upper': round(current_price * 1.05, 2),
                'bollinger_lower': round(current_price * 0.95, 2),
                'stochastic_k': round(np.random.uniform(0, 100), 2),
                'stochastic_d': round(np.random.uniform(0, 100), 2),
                'williams_r': round(np.random.uniform(-100, 0), 2),
                'cci': round(np.random.normal(0, 100), 2),
                'adx': round(np.random.uniform(0, 100), 2),
                'atr': round(current_price * 0.02, 4),
                'obv': round(np.random.uniform(1000000, 5000000), 0),
                'mfi': round(np.random.uniform(0, 100), 2),
                'roc': round(np.random.normal(0, 5), 2),
                'momentum': round(np.random.normal(0, 0.1), 4),
                'williams_alligator_blue': round(current_price * 0.98, 2),
                'williams_alligator_red': round(current_price * 1.02, 2),
                'williams_alligator_green': round(current_price * 1.01, 2),
                'fractal_high': round(current_price * 1.03, 2),
                'fractal_low': round(current_price * 0.97, 2),
                'gator_jaw': round(current_price * 0.99, 2),
                'gator_teeth': round(current_price * 1.005, 2),
                'gator_lips': round(current_price * 1.015, 2),
                'awesome_oscillator': round(np.random.normal(0, 0.1), 4),
                'accelerator_oscillator': round(np.random.normal(0, 0.05), 4),
                'force_index': round(np.random.normal(0, 1000000), 0),
                'ease_of_movement': round(np.random.normal(0, 0.1), 4),
                'commodity_channel_index': round(np.random.normal(0, 100), 2),
                'detrended_price_oscillator': round(np.random.normal(0, 0.1), 4),
                'klinger_oscillator': round(np.random.normal(0, 1000000), 0),
                'money_flow_index': round(np.random.uniform(0, 100), 2),
                'on_balance_volume': round(np.random.uniform(1000000, 5000000), 0),
                'percentage_price_oscillator': round(np.random.normal(0, 0.1), 4),
                'percentage_volume_oscillator': round(np.random.normal(0, 0.2), 4),
                'price_rate_of_change': round(np.random.normal(0, 5), 2),
                'relative_strength_index': round(rsi, 2),
                'stochastic_oscillator_k': round(np.random.uniform(0, 100), 2),
                'stochastic_oscillator_d': round(np.random.uniform(0, 100), 2),
                'triple_exponential_average': round(current_price * 1.01, 2),
                'ultimate_oscillator': round(np.random.uniform(0, 100), 2),
                'williams_percent_r': round(np.random.uniform(-100, 0), 2),
                'average_true_range': round(current_price * 0.02, 4),
                'average_directional_index': round(np.random.uniform(0, 100), 2),
                'commodity_channel_index': round(np.random.normal(0, 100), 2),
                'directional_movement_index': round(np.random.uniform(0, 100), 2),
                'minus_directional_movement': round(np.random.uniform(0, 100), 2),
                'plus_directional_movement': round(np.random.uniform(0, 100), 2),
                'minus_directional_indicator': round(np.random.uniform(0, 100), 2),
                'plus_directional_indicator': round(np.random.uniform(0, 100), 2),
                'parabolic_sar': round(current_price * 1.02, 2),
                'trend_intensity_index': round(np.random.uniform(0, 100), 2),
                'mass_index': round(np.random.uniform(0, 100), 2),
                'vortex_indicator_plus': round(np.random.uniform(0, 100), 2),
                'vortex_indicator_minus': round(np.random.uniform(0, 100), 2),
                'kst': round(np.random.normal(0, 0.1), 4),
                'kst_signal': round(np.random.normal(0, 0.1), 4),
                'ichimoku_a': round(current_price * 1.01, 2),
                'ichimoku_b': round(current_price * 0.99, 2),
                'ichimoku_base': round(current_price, 2),
                'ichimoku_conversion': round(current_price * 1.005, 2),
                'ichimoku_span_a': round(current_price * 1.015, 2),
                'ichimoku_span_b': round(current_price * 0.985, 2),
                'ichimoku_leading_span_a': round(current_price * 1.025, 2),
                'ichimoku_leading_span_b': round(current_price * 0.975, 2),
                'ichimoku_lagging_span': round(current_price * 0.995, 2),
                'aroon_up': round(np.random.uniform(0, 100), 2),
                'aroon_down': round(np.random.uniform(0, 100), 2),
                'aroon_oscillator': round(np.random.uniform(-100, 100), 2),
                'balance_of_power': round(np.random.normal(0, 0.1), 4),
                'chaikin_money_flow': round(np.random.normal(0, 0.1), 4),
                'chaikin_oscillator': round(np.random.normal(0, 1000000), 0),
                'donchian_channel_high': round(current_price * 1.05, 2),
                'donchian_channel_low': round(current_price * 0.95, 2),
                'donchian_channel_mid': round(current_price, 2),
                'keltner_channel_high': round(current_price * 1.03, 2),
                'keltner_channel_low': round(current_price * 0.97, 2),
                'keltner_channel_mid': round(current_price, 2),
                'ulcer_index': round(np.random.uniform(0, 10), 4),
                'guppy_multiple_moving_average_fast': round(current_price * 1.01, 2),
                'guppy_multiple_moving_average_slow': round(current_price * 0.99, 2),
                'hull_moving_average': round(current_price * 1.005, 2),
                'kaufman_adaptive_moving_average': round(current_price * 1.002, 2),
                'mcclellan_oscillator': round(np.random.normal(0, 100), 2),
                'mcclellan_summation_index': round(np.random.normal(0, 1000), 2),
                'mcclellan_ratio': round(np.random.uniform(0, 2), 4),
                'mcclellan_breadth_thrust': round(np.random.uniform(0, 1), 4),
                'mcclellan_oscillator_ratio': round(np.random.uniform(0, 2), 4),
                'mcclellan_summation_index_ratio': round(np.random.uniform(0, 2), 4),
                'mcclellan_breadth_thrust_ratio': round(np.random.uniform(0, 2), 4),
                'mcclellan_oscillator_thrust': round(np.random.uniform(0, 1), 4),
                'mcclellan_summation_index_thrust': round(np.random.uniform(0, 1), 4),
                'mcclellan_breadth_thrust_thrust': round(np.random.uniform(0, 1), 4),
                'mcclellan_oscillator_ratio_thrust': round(np.random.uniform(0, 1), 4),
                'mcclellan_summation_index_ratio_thrust': round(np.random.uniform(0, 1), 4),
                'mcclellan_breadth_thrust_ratio_thrust': round(np.random.uniform(0, 1), 4)
            })
        
        df = pd.DataFrame(data)
        logger.info(f"✅ Dados mock criados para HET: {len(df)} registros, {len(df.columns)} colunas")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara as features para predição"""
        if df.empty:
            logger.error("❌ DataFrame vazio, não é possível preparar features")
            return pd.DataFrame()
        
        logger.info(f"🔧 Preparando features de {len(df)} registros...")
        
        # Remove colunas que não são features
        exclude_cols = ['data', 'ativo', 'timestamp', 'date']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        logger.info(f"📊 Colunas disponíveis: {len(df.columns)}")
        logger.info(f"🔍 Features selecionadas: {len(feature_cols)}")
        
        # Seleciona apenas as features numéricas
        numeric_features = df[feature_cols].select_dtypes(include=[np.number])
        
        if numeric_features.empty:
            logger.error("❌ Nenhuma feature numérica encontrada")
            return pd.DataFrame()
        
        logger.info(f"📈 Features numéricas: {len(numeric_features.columns)} colunas")
        
        # Preenche valores NaN
        numeric_features = numeric_features.fillna(0)
        
        # Remove infinitos
        numeric_features = numeric_features.replace([np.inf, -np.inf], 0)
        
        # Pega apenas a última linha (dados mais recentes) para predição
        if len(numeric_features) > 0:
            latest_features = numeric_features.iloc[-1:].copy()
            logger.info(f"✅ Features preparadas: {len(latest_features.columns)} colunas")
            logger.debug(f"Colunas das features: {list(latest_features.columns)}")
            return latest_features
        else:
            logger.error("❌ Nenhuma linha válida encontrada após preparação")
            return pd.DataFrame()
    
    def predict_with_model(self, model_name: str, features: pd.DataFrame) -> Dict[str, Any]:
        """Faz predição com um modelo específico"""
        try:
            if features.empty:
                logger.error(f"❌ Nenhuma feature disponível para predição com {model_name}")
                return {"error": "Nenhuma feature disponível para predição"}
            
            model_info = self.model_manager.get_model_info(model_name)
            if not model_info:
                logger.error(f"❌ Modelo {model_name} não encontrado")
                return {"error": f"Modelo {model_name} não encontrado"}
            
            model = model_info["model"]
            model_type = model_info["info"]["model_type"]
            
            logger.info(f"🔮 Fazendo predição com {model_name} (tipo: {model_type})")
            
            # Faz a predição
            if model_type == "regressor":
                prediction = model.predict(features)
                result = {
                    "predicao": float(prediction[0]),
                    "modelo": model_name,
                    "tipo": "regressor",
                    "versao": model_info["info"]["timestamp"]
                }
                logger.info(f"✅ Predição regressora: {result['predicao']}")
                return result
                
            elif model_type == "classifier":
                prediction = model.predict(features)
                probabilities = model.predict_proba(features) if hasattr(model, 'predict_proba') else None
                
                result = {
                    "predicao": int(prediction[0]),
                    "probabilidade": float(probabilities[0][1]) if probabilities is not None else None,
                    "modelo": model_name,
                    "tipo": "classifier",
                    "versao": model_info["info"]["timestamp"]
                }
                logger.info(f"✅ Predição classificadora: {result['predicao']} (prob: {result['probabilidade']})")
                return result
            else:
                logger.error(f"❌ Tipo de modelo desconhecido: {model_type}")
                return {"error": f"Tipo de modelo desconhecido: {model_type}"}
                
        except Exception as e:
            logger.error(f"❌ Erro na predição com modelo {model_name}: {e}")
            return {"error": f"Erro na predição: {str(e)}"}
    
    def predict_all_models(self, symbol: str) -> Dict[str, Any]:
        """Faz predições com todos os modelos carregados usando dados reais"""
        try:
            logger.info(f"🚀 Iniciando predições para {symbol}...")
            
            # Obtém dados reais para o símbolo
            real_data = self.get_latest_data_for_symbol(symbol)
            
            if real_data.empty:
                logger.error(f"❌ Nenhum dado encontrado para o símbolo {symbol}")
                return {
                    "error": f"Nenhum dado encontrado para o símbolo {symbol}",
                    "symbol": symbol,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Prepara features dos dados reais
            features = self.prepare_features(real_data)
            
            if features.empty:
                logger.error(f"❌ Não foi possível preparar features para {symbol}")
                return {
                    "error": f"Não foi possível preparar features para {symbol}",
                    "symbol": symbol,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Lista de modelos carregados
            loaded_models = self.model_manager.list_loaded_models()
            
            if not loaded_models:
                logger.error("❌ Nenhum modelo carregado")
                return {
                    "error": "Nenhum modelo carregado",
                    "symbol": symbol,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            logger.info(f"📊 Modelos disponíveis: {loaded_models}")
            
            # Faz predições com todos os modelos
            predictions = {}
            successful_predictions = 0
            
            for model_name in loaded_models:
                logger.info(f"🔮 Processando modelo: {model_name}")
                result = self.predict_with_model(model_name, features)
                if "error" not in result:
                    predictions[model_name] = result
                    successful_predictions += 1
                    logger.info(f"✅ Predição bem-sucedida para {model_name}")
                else:
                    logger.warning(f"⚠️ Erro na predição para {model_name}: {result['error']}")
            
            logger.info(f"🎉 Predições concluídas: {successful_predictions}/{len(loaded_models)} modelos")
            
            return {
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat(),
                "modelos": predictions,
                "total_modelos": len(predictions),
                "dados_utilizados": f"Últimos {len(real_data)} registros",
                "features_utilizadas": len(features.columns)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na predição para símbolo {symbol}: {e}")
            return {
                "error": f"Erro na predição: {str(e)}",
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat()
            } 