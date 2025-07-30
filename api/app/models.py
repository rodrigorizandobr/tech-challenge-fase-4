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