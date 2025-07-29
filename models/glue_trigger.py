import os
import boto3
import json

def lambda_handler(event, context):
    """Lambda que triggera o Glue job de treinamento"""
    
    # Configurações
    glue_job_name = "cripto-model-training"
    
    try:
        # Cliente Glue
        glue = boto3.client('glue')
        
        # Iniciar Glue job
        response = glue.start_job_run(
            JobName=glue_job_name,
            Arguments={
                '--BUCKET': os.environ.get('BUCKET', 'criptos-data')
            }
        )
        
        job_run_id = response['JobRunId']
        
        print(f"Glue job iniciado: {glue_job_name} - Run ID: {job_run_id}")
        
        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "message": f"Glue job iniciado com sucesso",
                "job_name": glue_job_name,
                "job_run_id": job_run_id
            }
        }
        
    except Exception as e:
        print(f"Erro ao iniciar Glue job: {str(e)}")
        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "message": str(e)
            }
        } 