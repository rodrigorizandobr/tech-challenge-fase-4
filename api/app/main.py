from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
import os

from utils import ModelManager
from models import PredictionEngine

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

# Inicialização dos componentes
model_manager = ModelManager()
prediction_engine = PredictionEngine(model_manager)

# Variável global para controlar se os modelos foram carregados
models_loaded = False

@app.on_event("startup")
async def startup_event():
    """Carrega os modelos na inicialização da aplicação"""
    global models_loaded
    try:
        logger.info("🚀 Iniciando carregamento dos modelos...")
        loaded_models = model_manager.load_all_models()
        
        if loaded_models:
            models_loaded = True
            logger.info(f"✅ {len(loaded_models)} modelos carregados com sucesso!")
            logger.info(f"📊 Modelos disponíveis: {list(loaded_models.keys())}")
        else:
            logger.warning("⚠️ Nenhum modelo foi carregado!")
            
    except Exception as e:
        logger.error(f"❌ Erro ao carregar modelos: {e}")
        models_loaded = False

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
    global models_loaded
    
    status = "healthy" if models_loaded else "unhealthy"
    models_status = model_manager.get_models_status()
    
    return HealthResponse(
        status=status,
        models_loaded=models_loaded,
        total_models=models_status["total_models"],
        models=models_status["models"],
        versions=models_status["versions"]
    )

@app.get("/models", response_model=ModelsResponse, tags=["Models"])
async def list_models():
    """Lista todos os modelos carregados"""
    models_status = model_manager.get_models_status()
    
    return ModelsResponse(
        total_models=models_status["total_models"],
        models=models_status["models"],
        versions=models_status["versions"],
        last_loaded=models_status["last_loaded"]
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
        result = prediction_engine.predict_all_models(ativo)
        
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
        loaded_models = model_manager.load_all_models()
        
        if loaded_models:
            models_loaded = True
            return {
                "message": "Modelos recarregados com sucesso",
                "total_models": len(loaded_models),
                "models": list(loaded_models.keys())
            }
        else:
            models_loaded = False
            raise HTTPException(
                status_code=500,
                detail="Nenhum modelo foi carregado"
            )
            
    except Exception as e:
        logger.error(f"Erro ao recarregar modelos: {e}")
        models_loaded = False
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao recarregar modelos: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 