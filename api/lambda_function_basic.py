import json
import boto3
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis globais
s3_client = boto3.client("s3")
BUCKET_NAME = "criptos-data"

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
                    "timestamp": datetime.now().isoformat()
                })
            }
        
        elif path == '/health' and method == 'GET':
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
                    "total_models": 0,
                    "models": [],
                    "versions": {},
                    "timestamp": datetime.now().isoformat()
                })
            }
        
        elif path == '/models' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({
                    "total_models": 0,
                    "models": [],
                    "versions": {},
                    "last_loaded": datetime.now().isoformat(),
                    "message": "Modelos não carregados ainda"
                })
            }
        
        elif path.startswith('/symbol/') and method == 'GET':
            # Extrai o ativo da URL
            ativo = path.split('/')[-1]
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({
                    "ativo": ativo,
                    "timestamp": datetime.now().isoformat(),
                    "modelos": {
                        "regressor_rf": {
                            "predicao": 45000.50,
                            "modelo": "regressor_rf",
                            "tipo": "regressor",
                            "versao": "20250729-2130"
                        },
                        "classifier_rf": {
                            "predicao": 1,
                            "probabilidade": 0.75,
                            "modelo": "classifier_rf",
                            "tipo": "classifier",
                            "versao": "20250729-2130"
                        }
                    },
                    "total_modelos": 2,
                    "message": "Predições simuladas - modelos não carregados"
                })
            }
        
        elif path == '/reload' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({
                    "message": "Endpoint de reload - funcionalidade não implementada ainda",
                    "total_models": 0,
                    "models": [],
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
                        "/symbol/{ativo}",
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