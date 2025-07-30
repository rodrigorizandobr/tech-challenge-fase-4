import boto3
import joblib
import os
from typing import Dict, List, Any
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self, bucket_name: str = "criptos-data"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3")
        self.models: Dict[str, Any] = {}
        self.model_versions: Dict[str, str] = {}
        
    def list_model_files(self) -> List[str]:
        """Lista todos os arquivos .joblib na pasta models do S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
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
    
    def download_model(self, s3_key: str, local_path: str) -> bool:
        """Download de um modelo do S3"""
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"Modelo baixado: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao baixar modelo {s3_key}: {e}")
            return False
    
    def load_model(self, local_path: str) -> Any:
        """Carrega um modelo do arquivo local"""
        try:
            model = joblib.load(local_path)
            logger.info(f"Modelo carregado: {local_path}")
            return model
        except Exception as e:
            logger.error(f"Erro ao carregar modelo {local_path}: {e}")
            return None
    
    def extract_model_info(self, s3_key: str) -> Dict[str, str]:
        """Extrai informações do modelo baseado no nome do arquivo"""
        filename = s3_key.split('/')[-1]
        parts = filename.replace('.joblib', '').split('_')
        
        if len(parts) >= 3:
            model_type = parts[0]  # regressor, classifier
            model_name = parts[1]  # rf, gbr, lin, log
            timestamp = parts[2]    # timestamp
            
            return {
                "model_type": model_type,
                "model_name": model_name,
                "timestamp": timestamp,
                "full_name": f"{model_type}_{model_name}",
                "s3_key": s3_key
            }
        return {}
    
    def load_all_models(self) -> Dict[str, Any]:
        """Carrega todos os modelos do S3 na memória"""
        logger.info("Iniciando carregamento de todos os modelos...")
        
        model_files = self.list_model_files()
        if not model_files:
            logger.warning("Nenhum arquivo de modelo encontrado!")
            return {}
        
        loaded_models = {}
        
        for s3_key in model_files:
            model_info = self.extract_model_info(s3_key)
            if not model_info:
                continue
                
            model_name = model_info["full_name"]
            local_path = f"/tmp/{model_name}_{model_info['timestamp']}.joblib"
            
            # Download do modelo
            if self.download_model(s3_key, local_path):
                # Carrega o modelo
                model = self.load_model(local_path)
                if model:
                    loaded_models[model_name] = {
                        "model": model,
                        "info": model_info,
                        "loaded_at": datetime.utcnow().isoformat()
                    }
                    self.model_versions[model_name] = model_info["timestamp"]
                    
                    # Remove arquivo local
                    try:
                        os.remove(local_path)
                    except:
                        pass
        
        logger.info(f"Carregados {len(loaded_models)} modelos com sucesso")
        self.models = loaded_models
        return loaded_models
    
    def get_model(self, model_name: str) -> Any:
        """Retorna um modelo específico"""
        return self.models.get(model_name, {}).get("model")
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Retorna informações de um modelo específico"""
        return self.models.get(model_name, {})
    
    def list_loaded_models(self) -> List[str]:
        """Lista todos os modelos carregados"""
        return list(self.models.keys())
    
    def get_models_status(self) -> Dict[str, Any]:
        """Retorna status dos modelos carregados"""
        return {
            "total_models": len(self.models),
            "models": list(self.models.keys()),
            "versions": self.model_versions,
            "last_loaded": datetime.utcnow().isoformat()
        } 