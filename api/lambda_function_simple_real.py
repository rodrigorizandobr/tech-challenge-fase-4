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

def list_model_files():
    """Lista todos os arquivos .joblib na pasta models do S3"""
    try:
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix="models/",
            MaxKeys=100
        )
        
        model_files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].endswith('.joblib'):
                    model_files.append(obj['Key'])
        
        logger.info(f"Encontrados {len(model_files)} arquivos de modelo")
        return model_files
        
    except Exception as e:
        logger.error(f"Erro ao listar modelos: {e}")
        return []

def extract_model_info(s3_key):
    """Extrai informações do modelo baseado no nome do arquivo"""
    filename = s3_key.split('/')[-1]
    
    # Remove a extensão .joblib
    model_name = filename.replace('.joblib', '')
    
    # Determina o tipo do modelo baseado no nome
    model_type = "regressor"  # padrão
    
    if "LogReg" in model_name or "log" in model_name.lower():
        model_type = "classifier"
    elif "GradBoost" in model_name or "grad" in model_name.lower():
        model_type = "regressor"
    elif "LinReg" in model_name or "lin" in model_name.lower():
        model_type = "regressor"
    
    return {
        "model_type": model_type,
        "model_name": model_name,
        "timestamp": datetime.now().strftime("%Y%m%d-%H%M"),
        "full_name": model_name,
        "s3_key": s3_key
    }

def get_models_status():
    """Retorna o status dos modelos disponíveis"""
    try:
        model_files = list_model_files()
        
        models_info = []
        for s3_key in model_files:
            info = extract_model_info(s3_key)
            if info:
                models_info.append(info)
        
        return {
            "status": "available",
            "total_models": len(models_info),
            "models": [info["full_name"] for info in models_info],
            "versions": {info["full_name"]: info["timestamp"] for info in models_info},
            "last_loaded": datetime.now().isoformat(),
            "message": f"Encontrados {len(models_info)} modelos no S3"
        }
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

def predict_symbol_simple(symbol):
    """Faz predições simples para um símbolo específico"""
    try:
        logger.info(f"🔮 Fazendo predições para {symbol}...")
        
        # Simula predições baseadas nos modelos disponíveis
        model_files = list_model_files()
        
        if not model_files:
            return {
                "error": "Nenhum modelo encontrado no S3",
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
        
        # Cria predições simuladas baseadas nos modelos disponíveis
        predictions = {}
        for s3_key in model_files:
            model_info = extract_model_info(s3_key)
            if model_info:
                model_name = model_info["full_name"]
                model_type = model_info["model_type"]
                
                if model_type == "regressor":
                    predictions[model_name] = {
                        "predicao": 45000.50,  # Valor simulado
                        "modelo": model_name,
                        "tipo": "regressor",
                        "versao": model_info["timestamp"],
                        "status": "simulado"
                    }
                elif model_type == "classifier":
                    predictions[model_name] = {
                        "predicao": 1,  # Valor simulado
                        "probabilidade": 0.75,  # Valor simulado
                        "modelo": model_name,
                        "tipo": "classifier",
                        "versao": model_info["timestamp"],
                        "status": "simulado"
                    }
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "modelos": predictions,
            "total_modelos": len(predictions),
            "dados_utilizados": "Simulação - modelos não carregados",
            "message": "Predições simuladas - modelos não carregados no Lambda"
        }
        
    except Exception as e:
        logger.error(f"Erro na predição para {symbol}: {e}")
        return {
            "error": f"Erro na predição: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }

def handler(event, context):
    """Handler principal para AWS Lambda"""
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
                    "models_loaded": False,
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
                    "models_loaded": False,
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
            result = predict_symbol_simple(symbol)
            
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
            # Simula recarregamento dos modelos
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
                    "message": "Status dos modelos atualizado",
                    "success": True,
                    "models_loaded": False,
                    "models_available": status["total_models"],
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