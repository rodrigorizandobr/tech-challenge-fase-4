import json
import boto3
import logging
from datetime import datetime
import sys
import os

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis globais
s3_client = boto3.client("s3")
BUCKET_NAME = "criptos-data"

# Cache global para modelos
model_manager = None
prediction_engine = None
models_loaded = False

def load_models():
    """Carrega todos os modelos do S3"""
    global model_manager, prediction_engine, models_loaded
    
    try:
        logger.info("🚀 Iniciando carregamento dos modelos...")
        
        # Importa as classes necessárias
        from app.utils import ModelManager
        from app.models import PredictionEngine
        
        # Inicializa o model manager
        model_manager = ModelManager(BUCKET_NAME)
        
        # Carrega todos os modelos
        loaded_models = model_manager.load_all_models()
        
        if loaded_models:
            # Inicializa o prediction engine
            prediction_engine = PredictionEngine(model_manager)
            models_loaded = True
            logger.info(f"✅ {len(loaded_models)} modelos carregados com sucesso!")
            return True
        else:
            logger.warning("⚠️ Nenhum modelo foi carregado")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao carregar modelos: {e}")
        return False

def get_models_status():
    """Retorna o status dos modelos carregados"""
    global model_manager, models_loaded
    
    if not models_loaded or not model_manager:
        return {
            "status": "not_loaded",
            "total_models": 0,
            "models": [],
            "versions": {},
            "last_loaded": datetime.now().isoformat(),
            "message": "Modelos não carregados"
        }
    
    try:
        status = model_manager.get_models_status()
        status["status"] = "loaded"
        return status
    except Exception as e:
        logger.error(f"Erro ao obter status dos modelos: {e}")
        return {
            "status": "error",
            "total_models": 0,
            "models": [],
            "versions": {},
            "last_loaded": datetime.now().isoformat(),
            "message": f"Erro ao obter status: {str(e)}"
        }

def predict_symbol(symbol: str):
    """Faz predições para um símbolo específico"""
    global prediction_engine, models_loaded
    
    if not models_loaded or not prediction_engine:
        return {
            "error": "Modelos não carregados",
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "message": "Execute /reload para carregar os modelos"
        }
    
    try:
        logger.info(f"🔮 Fazendo predições para {symbol}...")
        result = prediction_engine.predict_all_models(symbol)
        return result
    except Exception as e:
        logger.error(f"Erro na predição para {symbol}: {e}")
        return {
            "error": f"Erro na predição: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }

def handler(event, context):
    """Handler principal para AWS Lambda"""
    global models_loaded
    
    try:
        logger.info("🚀 Iniciando processamento da requisição...")
        
        # Extrai informações da requisição
        path = event.get('path', '/')
        method = event.get('httpMethod', 'GET')
        
        logger.info(f"📝 Path: {path}, Method: {method}")
        
        # Roteamento básico
        if path == '/' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({
                    "message": "Cripto Prediction API",
                    "version": "1.0.0",
                    "status": "running",
                    "models_loaded": models_loaded,
                    "timestamp": datetime.now().isoformat(),
                    "endpoints": [
                        "/",
                        "/health",
                        "/models", 
                        "/symbol/{symbol}",
                        "/reload"
                    ]
                })
            }
        
        elif path == '/health' and method == 'GET':
            status = get_models_status()
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({
                    "status": "healthy",
                    "models_loaded": models_loaded,
                    **status
                })
            }
        
        elif path == '/models' and method == 'GET':
            status = get_models_status()
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps(status)
            }
        
        elif path.startswith('/symbol/') and method == 'GET':
            # Extrai o símbolo da URL
            symbol = path.split('/')[-1]
            
            # Faz as predições
            result = predict_symbol(symbol)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps(result)
            }
        
        elif path == '/reload' and method == 'GET':
            # Recarrega os modelos
            success = load_models()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({
                    "message": "Modelos recarregados" if success else "Erro ao recarregar modelos",
                    "success": success,
                    "models_loaded": models_loaded,
                    "timestamp": datetime.now().isoformat()
                })
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({
                    "error": "Endpoint não encontrado",
                    "path": path,
                    "method": method,
                    "available_endpoints": [
                        "/",
                        "/health", 
                        "/models",
                        "/symbol/{symbol}",
                        "/reload"
                    ]
                })
            }
            
    except Exception as e:
        logger.error(f"❌ Erro no handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Erro interno do servidor',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

# Carrega os modelos na inicialização (cold start)
if not models_loaded:
    load_models() 