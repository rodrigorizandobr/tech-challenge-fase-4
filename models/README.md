# Pipeline de ML para Criptomoedas - Terraform

Este diretório contém a infraestrutura Terraform para criar um pipeline automatizado de Machine Learning para análise de criptomoedas.

## 🏗️ Arquitetura

```
S3 (raw.csv alterado) 
    ↓ (trigger)
Lambda (feature_engineering.py)
    ↓ (salva features)
S3 (features alterado)
    ↓ (trigger)
Lambda (glue_trigger.py)
    ↓ (inicia)
Glue (train_models_glue.py)
    ↓ (salva modelos)
S3 (artifacts)
```

## 📁 Estrutura de Arquivos

- `main.tf` - Recursos principais da infraestrutura
- `variables.tf` - Variáveis do Terraform
- `outputs.tf` - Outputs da infraestrutura
- `feature_engineering.py` - Lambda para engenharia de features
- `train_models_lambda.py` - Lambda para treinamento de modelos
- `train_models.py` - Versão original (não usada)

## 🚀 Deploy

### Pré-requisitos

1. AWS CLI configurado
2. Terraform instalado
3. Permissões adequadas na AWS

### Comandos

```bash
# Inicializar Terraform
terraform init

# Verificar plano
terraform plan

# Aplicar infraestrutura
terraform apply

# Para destruir (cuidado!)
terraform destroy
```

## ⚙️ Configuração

### Variáveis Disponíveis

- `aws_region` - Região AWS (padrão: us-east-1)
- `s3_bucket_name` - Nome do bucket S3 (padrão: criptos-data)
- `environment` - Ambiente (padrão: dev)
- `project` - Nome do projeto (padrão: cripto-ml-pipeline)

### Personalizar

```bash
# Usar variáveis customizadas
terraform apply -var="s3_bucket_name=meu-bucket-cripto" -var="aws_region=us-west-2"
```

## 📊 Recursos Criados

### S3
- Bucket para dados (`criptos-data`)
- Versionamento habilitado
- Bloqueio de acesso público

### Lambda Functions
- `cripto-feature-engineering` - Processa features
- `cripto-glue-trigger` - Inicia Glue job

### Glue Jobs
- `cripto-model-training` - Treina modelos

### IAM
- Roles para Lambda e Glue
- Políticas de acesso ao S3

### CloudWatch
- Log groups para monitoramento
- Retenção de 14 dias

### Triggers
- S3 → Lambda (automático)
- Processamento em cascata

## 🔄 Fluxo de Dados

1. **Upload de dados brutos** para `s3://bucket/raw.csv`
2. **Trigger automático** do Lambda de features
3. **Processamento** e salvamento de features em `s3://bucket/features/`
4. **Trigger automático** do Lambda de treinamento
5. **Treinamento** e salvamento de modelos em `s3://bucket/models/`

## 📈 Monitoramento

### CloudWatch Logs
- `/aws/lambda/cripto-feature-engineering`
- `/aws/lambda/cripto-glue-trigger`
- `/aws-glue/jobs/cripto-model-training`

### Métricas Importantes
- Duração de execução
- Taxa de erro
- Uso de memória

## 💰 Custos Estimados

- **Lambda Features**: ~$0.01 por execução
- **Lambda Trigger**: ~$0.001 por execução
- **Glue Training**: ~$0.44/hora × (20/60) = ~$0.15
- **S3**: ~$0.023/GB/mês
- **CloudWatch**: ~$0.50/GB de logs

**Total por pipeline**: ~$0.16 + storage

## 🛠️ Troubleshooting

### Problemas Comuns

1. **Timeout do Lambda**
   - Aumentar `timeout` no Terraform
   - Otimizar código

2. **Erro de permissão**
   - Verificar IAM roles
   - Confirmar políticas

3. **Trigger não funciona**
   - Verificar configuração do S3
   - Confirmar permissões Lambda

### Logs Úteis

```bash
# Ver logs do Lambda features
aws logs tail /aws/lambda/cripto-feature-engineering --follow

# Ver logs do Lambda trigger
aws logs tail /aws/lambda/cripto-glue-trigger --follow

# Ver logs do Glue job
aws logs tail /aws-glue/jobs/cripto-model-training --follow
```

## 🔧 Manutenção

### Atualizar Código
```bash
# Re-aplicar após mudanças no código
terraform apply
```

### Backup
- Dados: S3 versioning
- Modelos: S3 com versioning
- Infraestrutura: Terraform state

## 📝 Notas

- Pipeline totalmente automatizado
- Processamento event-driven
- Escalável conforme demanda
- Custo otimizado
- Monitoramento integrado 