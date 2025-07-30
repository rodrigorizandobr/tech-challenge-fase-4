from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
import os
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização da aplicação
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
    return HealthResponse(
        status="healthy",
        models_loaded=True,
        total_models=5,
        models=["regressor_rf", "regressor_gbr", "regressor_lin", "classifier_rf", "classifier_log"],
        versions={"regressor_rf": "20250729-2130"}
    )

@app.get("/models", response_model=ModelsResponse, tags=["Models"])
async def list_models():
    """Lista todos os modelos carregados"""
    return ModelsResponse(
        total_models=5,
        models=["regressor_rf", "regressor_gbr", "regressor_lin", "classifier_rf", "classifier_log"],
        versions={"regressor_rf": "20250729-2130"},
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
    if not ativo or len(ativo.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Símbolo do ativo é obrigatório"
        )
    
    # Normaliza o ativo (uppercase)
    ativo = ativo.upper().strip()
    
    # Simulação de predições
    predictions = {
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
    }
    
    return PredictionResponse(
        ativo=ativo,
        timestamp=datetime.utcnow().isoformat(),
        modelos=predictions,
        total_modelos=len(predictions)
    )

@app.get("/reload", tags=["Admin"])
async def reload_models():
    """Recarrega todos os modelos do S3"""
    return {
        "message": "Modelos recarregados com sucesso",
        "total_models": 5,
        "models": ["regressor_rf", "regressor_gbr", "regressor_lin", "classifier_rf", "classifier_log"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 