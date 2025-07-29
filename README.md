# 📈 Tech Challenge - Fase 4 FIAP 
## Pipeline de Modelagem para Cripto Ativos

Projeto em **Python 3.11** que automatiza todo o ciclo de vida de modelos de _machine learning_ para criptoativos, do _raw data_ no S3 até a exposição dos modelos prontos para consulta via API.

| Etapa | Serviço AWS | Script/Job | Saída |
|-------|-------------|------------|-------|
| Ingestão diária `raw.csv` | S3 (prefixo `raw/`) | — | `raw.csv` |
| **Feature Engineering** | Lambda (+ EventBridge) ou Glue Job | `feature_job.py` | `features/cripto_features_<YYYYMMDD>.parquet` <br>e `features/cripto_features_latest.parquet` |
| **Treino + Avaliação** | Lambda / ECS / local | `train_models.py` | Artefatos `artifacts/*.joblib` |
| **Exportação** | Lambda / Step Functions | `export_models.py` | `models/<timestamp>.joblib` <br>e `models/latest/*.joblib` |
| **Consumo** | API REST/GraphQL | (fora do escopo) | Previsões p/ código do ativo |

---

## ✨ Principais funcionalidades

* **Pré‑processamento robusto** — Lags, retornos, volatilidades, indicadores de candle, IQR, ATR, z‑score robusto e muito mais.  
* **Modelos híbridos** — Três regressões (Linear, Gradient Boosting, Random Forest) e duas classificações (Logistic, Random Forest) avaliados em _TimeSeriesSplit_.  
* **Infra‑as‑code friendly** — Todos os passos encapsulados em scripts idempotentes; prontos para orquestração em Terraform/CDK.  
* **Artefatos versionados** — Nome de arquivo inclui timestamp ISO; atalho `latest/` facilita _hot reload_ na API.  
* **Compatível com Parquet** — Salva features em Parquet _snappy_ (80 %+ economia de I/O).  

---

## 📂 Estrutura do repositório

```
.
├── scripts/
│   ├── feature_job.py      # gera features diárias a partir do raw.csv
│   ├── train_models.py     # treina e avalia modelos
│   ├── export_models.py    # faz upload dos modelos ao S3
│   └── build_docker.sh     # imagem Lambda/ECS com dependências
├── artifacts/              # modelos .joblib (criado em runtime)
├── requirements.txt
└── README.md
```

---

## 🛠️ Requisitos

| Ferramenta | Versão |
|------------|--------|
| Python | ≥ 3.11 |
| AWS CLI | ≥ 2.0 |
| Docker | opcional para empacotar Lambda |
| Bibliotecas | ver `requirements.txt` |

Crie e ative um _virtual env_, depois:

```bash
pip install -r requirements.txt
```

---

## ⚡ Como executar localmente

> ⚠️ Garanta que suas credenciais AWS possuam `s3:GetObject`, `s3:PutObject` e `s3:CopyObject` no bucket `criptos-data`.

1. **Baixar o dataset de features (opcional)**  
   ```bash
   aws s3 cp s3://criptos-data/features/cripto_features_latest.parquet ./data/
   ```

2. **Treinar modelos**  
   ```bash
   python scripts/train_models.py
   # artefatos criados em ./artifacts
   ```

3. **Exportar para S3**  
   ```bash
   python scripts/export_models.py
   # modelos disponíveis em s3://criptos-data/models/
   ```

---

## 🚀 Desdobramentos em produção

* **EventBridge → Lambda**    para _feature_job.py_ (datasets até ~1 GB/dia).  
* **Glue Job**                para volumes maiores ou _sparkification_.  
* **Step Functions**          orquestra **Feature → Train → Export** em DAG com retries.  
* **API**                     FastAPI em Lambda/ECS baixa `models/latest/*.joblib` on‑cold‑start e fornece `/predict?ativo=BTC`.

---

## 🧪 Testes rápidos

```bash
python - <<'PY'
import boto3, joblib, io
s3 = boto3.client("s3")
buf = io.BytesIO()
s3.download_fileobj("criptos-data", "models/latest/regressor_rf.joblib", buf)
buf.seek(0)
model = joblib.load(buf)
print("Modelo carregado:", model)
PY
```

---

## 🤝 Contribuindo

1. Faça um _fork_ e crie sua _feature branch_.  
2. Abra um _pull‑request_ com descrição clara do problema / melhoria.  
3. Siga o padrão _black_ (`black .`) e _isort_.  
4. Documente alterações no **CHANGELOG** (a criar).

---

## 📜 Licença

Distribuído sob licença **MIT**. Veja `LICENSE` para mais detalhes.
