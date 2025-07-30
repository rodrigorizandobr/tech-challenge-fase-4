import json
import boto3
import joblib
import os
from typing import Dict, Any, List
from datetime import datetime
import logging
from mangum import Mangum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="Cripto Prediction API",
    description="API para predições de criptomoedas usando modelos ML",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para validação
class PredictionResponse(BaseModel):
    ativo: str
    timestamp: str
    modelos: Dict[str, Any]
    total_modelos: int

class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    total_models: int
    models: List[str]
    versions: Dict[str, str]

class ModelsResponse(BaseModel):
    total_models: int
    models: List[str]
    versions: Dict[str, str]
    last_loaded: str

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
                
                # Remove arquivo temporário
                os.remove(temp_path)
                
            except Exception as e:
                logger.error(f"❌ Erro ao carregar modelo {s3_key}: {e}")
                continue
        
        models_loaded = len(models_cache) > 0
        logger.info(f"🎉 Carregados {len(models_cache)} modelos com sucesso!")
        return models_loaded
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar modelos: {e}")
        return False

def predict_with_models(ativo: str) -> Dict[str, Any]:
    """Faz predições com todos os modelos carregados"""
    global models_cache
    
    if not models_cache:
        return {
            "error": "Nenhum modelo carregado",
            "ativo": ativo,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Simulação de features (em produção viria de dados reais)
    import numpy as np
    features = np.random.rand(1, 50)  # 50 features simuladas
    
    predictions = {}
    
    for model_name, model in models_cache.items():
        try:
            # Faz predição
            prediction = model.predict(features)
            
            # Determina tipo do modelo
            model_type = "regressor" if "regressor" in model_name else "classifier"
            
            result = {
                "predicao": float(prediction[0]),
                "modelo": model_name,
                "tipo": model_type,
                "versao": "20250729-2130"
            }
            
            # Adiciona probabilidade para classificadores
            if model_type == "classifier" and hasattr(model, 'predict_proba'):
                proba = model.predict_proba(features)
                result["probabilidade"] = float(proba[0][1])
            
            predictions[model_name] = result
            
        except Exception as e:
            logger.error(f"❌ Erro na predição com modelo {model_name}: {e}")
            continue
    
    return {
        "ativo": ativo,
        "timestamp": datetime.utcnow().isoformat(),
        "modelos": predictions,
        "total_modelos": len(predictions)
    }

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz"""
    return {
        "message": "Cripto Prediction API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Verifica o status da API e dos modelos"""
    global models_loaded, models_cache
    
    status = "healthy" if models_loaded else "unhealthy"
    
    return HealthResponse(
        status=status,
        models_loaded=models_loaded,
        total_models=len(models_cache),
        models=list(models_cache.keys()),
        versions={name: "20250729-2130" for name in models_cache.keys()}
    )

@app.get("/models", response_model=ModelsResponse, tags=["Models"])
async def list_models():
    """Lista todos os modelos carregados"""
    global models_cache
    
    return ModelsResponse(
        total_models=len(models_cache),
        models=list(models_cache.keys()),
        versions={name: "20250729-2130" for name in models_cache.keys()},
        last_loaded=datetime.utcnow().isoformat()
    )

@app.get("/symbol/{ativo}", response_model=PredictionResponse, tags=["Predictions"])
async def predict_symbol(ativo: str):
    """
    Faz predições para um ativo específico usando todos os modelos carregados
    
    Args:
        ativo: Símbolo do ativo (ex: BTC, ETH, etc.)
    
    Returns:
        Predições de todos os modelos para o ativo
    """
    global models_loaded
    
    if not models_loaded:
        raise HTTPException(
            status_code=503, 
            detail="Modelos não carregados. Tente novamente em alguns segundos."
        )
    
    if not ativo or len(ativo.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Símbolo do ativo é obrigatório"
        )
    
    # Normaliza o ativo (uppercase)
    ativo = ativo.upper().strip()
    
    try:
        # Faz predições com todos os modelos
        result = predict_with_models(ativo)
        
        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )
        
        return PredictionResponse(
            ativo=result["ativo"],
            timestamp=result["timestamp"],
            modelos=result["modelos"],
            total_modelos=result["total_modelos"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na predição para {ativo}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na predição: {str(e)}"
        )

@app.get("/reload", tags=["Admin"])
async def reload_models():
    """Recarrega todos os modelos do S3"""
    global models_loaded
    
    try:
        logger.info("🔄 Recarregando modelos...")
        success = load_models_from_s3()
        
        if success:
            return {
                "message": "Modelos recarregados com sucesso",
                "total_models": len(models_cache),
                "models": list(models_cache.keys())
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Nenhum modelo foi carregado"
            )
            
    except Exception as e:
        logger.error(f"Erro ao recarregar modelos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao recarregar modelos: {str(e)}"
        )

# Carrega modelos na inicialização
@app.on_event("startup")
async def startup_event():
    """Carrega os modelos na inicialização da aplicação"""
    load_models_from_s3()

# Handler para AWS Lambda
handler = Mangum(app) 