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
            logger.info(f"Listando modelos no bucket {self.bucket_name}...")
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
                        logger.info(f"Encontrado modelo: {obj['Key']}")
            
            logger.info(f"Encontrados {len(model_files)} arquivos de modelo")
            return model_files
            
        except Exception as e:
            logger.error(f"Erro ao listar modelos: {e}")
            return []
    
    def download_model(self, s3_key: str, local_path: str) -> bool:
        """Download de um modelo do S3"""
        try:
            logger.info(f"Baixando modelo: {s3_key}")
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"Modelo baixado com sucesso: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao baixar modelo {s3_key}: {e}")
            return False
    
    def load_model(self, local_path: str) -> Any:
        """Carrega um modelo do arquivo local"""
        try:
            logger.info(f"Carregando modelo: {local_path}")
            model = joblib.load(local_path)
            logger.info(f"Modelo carregado com sucesso: {local_path}")
            return model
        except Exception as e:
            logger.error(f"Erro ao carregar modelo {local_path}: {e}")
            return None
    
    def extract_model_info(self, s3_key: str) -> Dict[str, str]:
        """Extrai informações do modelo baseado no nome do arquivo"""
        filename = s3_key.split('/')[-1]
        parts = filename.replace('.joblib', '').split('_')
        
        # Padrão esperado: {tipo}_{algoritmo}_{timestamp}.joblib
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
        # Padrão alternativo: {algoritmo}.joblib (para modelos existentes)
        elif len(parts) == 1:
            model_name = parts[0]
            
            # Mapear nomes para tipos
            model_type_map = {
                "GradBoost": "regressor",
                "LinReg": "regressor", 
                "LogReg": "classifier",
                "RandomForest": "regressor",
                "SVM": "classifier"
            }
            
            model_type = model_type_map.get(model_name, "regressor")
            timestamp = "20250729-2130"  # Timestamp padrão
            
            return {
                "model_type": model_type,
                "model_name": model_name.lower(),
                "timestamp": timestamp,
                "full_name": f"{model_type}_{model_name.lower()}",
                "s3_key": s3_key
            }
        else:
            logger.warning(f"Nome de arquivo não segue padrão esperado: {filename}")
            return {}
    
    def load_all_models(self) -> Dict[str, Any]:
        """Carrega todos os modelos do S3 na memória"""
        logger.info("🚀 Iniciando carregamento de todos os modelos...")
        
        model_files = self.list_model_files()
        if not model_files:
            logger.warning("⚠️ Nenhum arquivo de modelo encontrado!")
            return {}
        
        loaded_models = {}
        
        for s3_key in model_files:
            logger.info(f"Processando modelo: {s3_key}")
            model_info = self.extract_model_info(s3_key)
            if not model_info:
                logger.warning(f"Pulando modelo com formato inválido: {s3_key}")
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
                    logger.info(f"✅ Modelo carregado: {model_name}")
                    
                    # Remove arquivo local
                    try:
                        os.remove(local_path)
                        logger.debug(f"Arquivo temporário removido: {local_path}")
                    except Exception as e:
                        logger.warning(f"Erro ao remover arquivo temporário {local_path}: {e}")
                else:
                    logger.error(f"❌ Falha ao carregar modelo: {model_name}")
            else:
                logger.error(f"❌ Falha ao baixar modelo: {s3_key}")
        
        logger.info(f"🎉 Carregados {len(loaded_models)} modelos com sucesso")
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