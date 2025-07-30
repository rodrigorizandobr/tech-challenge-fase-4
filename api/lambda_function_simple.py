import json
import boto3
import joblib
import os
from datetime import datetime
import logging
from flask import Flask, jsonify, request

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização da aplicação Flask
app = Flask(__name__)

# Variáveis globais para cache dos modelos
models_cache = {}
models_loaded = False
s3_client = boto3.client("s3")
BUCKET_NAME = "criptos-data"

def load_models_from_s3():
    """Carrega todos os modelos .joblib do S3"""
    global models_cache, models_loaded
    
    try:
        logger.info("🚀 Iniciando carregamento dos modelos do S3...")
        
        # Lista arquivos .joblib no bucket
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
        
        logger.info(f"📁 Encontrados {len(model_files)} arquivos de modelo")
        
        if not model_files:
            logger.warning("⚠️ Nenhum arquivo de modelo encontrado!")
            return False
        
        # Carrega cada modelo
        for s3_key in model_files:
            try:
                # Download temporário
                temp_path = f"/tmp/{s3_key.split('/')[-1]}"
                s3_client.download_file(BUCKET_NAME, s3_key, temp_path)
                
                # Carrega o modelo
                model = joblib.load(temp_path)
                
                # Extrai nome do modelo
                model_name = s3_key.split('/')[-1].replace('.joblib', '')
                models_cache[model_name] = model
                
                logger.info(f"✅ Modelo carregado: {model_name}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao carregar modelo {s3_key}: {e}")
                continue
        
        models_loaded = len(models_cache) > 0
        logger.info(f"🎯 Total de modelos carregados: {len(models_cache)}")
        return models_loaded
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar modelos: {e}")
        return False

def predict_with_models(ativo: str):
    """Faz predições usando todos os modelos carregados"""
    try:
        predictions = {}
        
        for model_name, model in models_cache.items():
            try:
                # Simula dados de entrada (em produção, você carregaria dados reais)
                # Aqui estamos apenas simulando uma predição
                if 'regressor' in model_name:
                    prediction = 45000.50  # Simulação
                    predictions[model_name] = {
                        "predicao": prediction,
                        "modelo": model_name,
                        "tipo": "regressor",
                        "versao": "20250729-2130"
                    }
                elif 'classifier' in model_name:
                    prediction = 1  # Simulação
                    probability = 0.75  # Simulação
                    predictions[model_name] = {
                        "predicao": prediction,
                        "probabilidade": probability,
                        "modelo": model_name,
                        "tipo": "classifier",
                        "versao": "20250729-2130"
                    }
                    
            except Exception as e:
                logger.error(f"❌ Erro na predição com modelo {model_name}: {e}")
                continue
        
        return predictions
        
    except Exception as e:
        logger.error(f"❌ Erro geral na predição: {e}")
        return {}

@app.route('/', methods=['GET'])
def root():
    """Endpoint raiz"""
    return jsonify({
        "message": "Cripto Prediction API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "models_loaded": models_loaded,
        "total_models": len(models_cache),
        "models": list(models_cache.keys()),
        "versions": {
            "regressor_rf": "20250729-2130",
            "classifier_rf": "20250729-2130"
        }
    })

@app.route('/models', methods=['GET'])
def list_models():
    """Lista modelos disponíveis"""
    return jsonify({
        "total_models": len(models_cache),
        "models": list(models_cache.keys()),
        "versions": {
            "regressor_rf": "20250729-2130"
        },
        "last_loaded": datetime.now().isoformat()
    })

@app.route('/symbol/<ativo>', methods=['GET'])
def predict_symbol(ativo):
    """Endpoint de predição para um ativo"""
    try:
        if not models_loaded:
            return jsonify({
                "error": "Modelos não carregados",
                "message": "Execute /reload para carregar os modelos"
            }), 500
        
        predictions = predict_with_models(ativo)
        
        if not predictions:
            return jsonify({
                "error": "Erro na predição",
                "message": "Não foi possível fazer predições"
            }), 500
        
        return jsonify({
            "ativo": ativo,
            "timestamp": datetime.now().isoformat(),
            "modelos": predictions,
            "total_modelos": len(predictions)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no endpoint de predição: {e}")
        return jsonify({
            "error": "Erro interno",
            "message": str(e)
        }), 500

@app.route('/reload', methods=['GET'])
def reload_models():
    """Recarrega os modelos do S3"""
    try:
        success = load_models_from_s3()
        
        if success:
            return jsonify({
                "message": "Modelos recarregados com sucesso",
                "total_models": len(models_cache),
                "models": list(models_cache.keys())
            })
        else:
            return jsonify({
                "error": "Erro ao recarregar modelos",
                "message": "Verifique os logs para mais detalhes"
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Erro ao recarregar modelos: {e}")
        return jsonify({
            "error": "Erro interno",
            "message": str(e)
        }), 500

# Handler para Lambda
def handler(event, context):
    """Handler principal para AWS Lambda"""
    try:
        # Carrega modelos na primeira execução
        if not models_loaded:
            load_models_from_s3()
        
        # Processa a requisição
        with app.test_client() as client:
            # Extrai path e method do evento
            path = event.get('path', '/')
            method = event.get('httpMethod', 'GET')
            
            # Faz a requisição
            response = client.open(path=path, method=method)
            
            return {
                'statusCode': response.status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': response.get_data(as_text=True)
            }
            
    except Exception as e:
        logger.error(f"❌ Erro no handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Erro interno do servidor',
                'message': str(e)
            })
        }

if __name__ == '__main__':
    app.run(debug=True) 