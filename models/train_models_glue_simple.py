#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, warnings, joblib
from pathlib import Path
from datetime import datetime
import boto3, pandas as pd, numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, accuracy_score,
    f1_score, roc_auc_score
)
from awsglue.utils import getResolvedOptions

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------- Configurações do Glue ----------
args = getResolvedOptions(sys.argv, ['BUCKET_NAME'])
BUCKET = args['BUCKET_NAME']
FEATURES_KEY = "cripto_features.csv"
LOCAL_FEATURES = "/tmp/cripto_features.csv"
ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True, parents=True)

# ---------- Utilidades ----------
def download_from_s3(bucket, key, local_path):
    s3 = boto3.client("s3")
    s3.download_file(bucket, key, local_path)

def time_stamp():
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")

# ---------- 1) Leitura do dataset ----------
print("Baixando dataset de features...")
download_from_s3(BUCKET, FEATURES_KEY, LOCAL_FEATURES)
df = pd.read_csv(LOCAL_FEATURES, sep="|")  # Corrigido para usar separador '|'
print("Linhas lidas:", len(df))

# ---------- 2) Targets & seleção de features ----------
df = df.sort_values(["data", "ativo"]).reset_index(drop=True)
df["fechamento_next"] = df.groupby("ativo")["fechamento"].shift(-1)
df["direction_next"]  = (df["fechamento_next"] > df["fechamento"]).astype(int)
df_model = df.dropna(subset=["fechamento_next"]).copy()

cols_excluir = [
    "data", "fechamento_next", "direction_next", "max_acum"
]
cat_cols = ["ativo"]
num_cols = [c for c in df_model.columns if c not in cols_excluir + cat_cols]

for c in num_cols:
    df_model[c] = pd.to_numeric(df_model[c], errors="coerce")

X = df_model[cat_cols + num_cols]
y_reg = df_model["fechamento_next"]
y_clf = df_model["direction_next"]

# ---------- 3) Pré‑processamento ----------
cat_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("ohe", OneHotEncoder(handle_unknown="ignore", sparse=False))
])

num_transformer_tree = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
])

num_transformer_linear = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

preprocess_tree = ColumnTransformer([
    ("cat", cat_transformer, cat_cols),
    ("num", num_transformer_tree, num_cols),
])

preprocess_linear = ColumnTransformer([
    ("cat", cat_transformer, cat_cols),
    ("num", num_transformer_linear, num_cols),
])

# ---------- 4) Modelos ----------
reg_lin = Pipeline([("prep", preprocess_linear), ("model", LinearRegression())])
reg_gbr = Pipeline([("prep", preprocess_tree), ("model", GradientBoostingRegressor(random_state=42))])
reg_rf  = Pipeline([("prep", preprocess_tree), ("model", RandomForestRegressor(
    n_estimators=400, random_state=42, n_jobs=-1))])

clf_log = Pipeline([("prep", preprocess_linear), ("model", LogisticRegression(max_iter=1000))])
clf_rf  = Pipeline([("prep", preprocess_tree), ("model", RandomForestClassifier(
    n_estimators=400, class_weight="balanced", random_state=42, n_jobs=-1))])

tscv = TimeSeriesSplit(n_splits=5)

# ---------- 5) Avaliação ----------
def eval_reg(pipe):
    maes, rmses, mapes = [], [], []
    for tr_idx, te_idx in tscv.split(X):
        X_tr, X_te = X.iloc[tr_idx], X.iloc[te_idx]
        y_tr, y_te = y_reg.iloc[tr_idx], y_reg.iloc[te_idx]
        pipe.fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        maes.append(mean_absolute_error(y_te, pred))
        rmses.append(np.sqrt(mean_squared_error(y_te, pred)))
        denom = np.where(y_te == 0, np.nan, y_te)
        mapes.append(np.nanmean(np.abs((y_te - pred)/denom))*100)
    return np.mean(maes), np.mean(rmses), np.nanmean(mapes)

def eval_clf(pipe):
    accs, f1s, aucs = [], [], []
    for tr_idx, te_idx in tscv.split(X):
        X_tr, X_te = X.iloc[tr_idx], X.iloc[te_idx]
        y_tr, y_te = y_clf.iloc[tr_idx], y_clf.iloc[te_idx]
        pipe.fit(X_tr, y_tr)
        proba = pipe.predict_proba(X_te)[:,1] if hasattr(pipe[-1], "predict_proba") else None
        pred  = pipe.predict(X_te)
        accs.append(accuracy_score(y_te, pred))
        f1s.append(f1_score(y_te, pred))
        if proba is not None:
            aucs.append(roc_auc_score(y_te, proba))
    return np.mean(accs), np.mean(f1s), np.mean(aucs)

print("\n--- Regressão ---")
for name, model in [("LinReg", reg_lin), ("GradBoost", reg_gbr), ("RandForest", reg_rf)]:
    mae, rmse, mape = eval_reg(model)
    print(f"{name:<11}  MAE={mae:.3f}  RMSE={rmse:.3f}  MAPE={mape:.2f}%")

print("\n--- Classificação ---")
for name, model in [("LogReg", clf_log), ("RandForest", clf_rf)]:
    acc, f1, auc = eval_clf(model)
    print(f"{name:<11}  ACC={acc:.3f}  F1={f1:.3f}  AUC={auc:.3f}")

# ---------- 6) Treino final em todo o histórico ----------
print("\nTreinando modelos finais...")
final_models = {
    "regressor_rf":  reg_rf.fit(X, y_reg),
    "regressor_gbr": reg_gbr.fit(X, y_reg),
    "regressor_lin": reg_lin.fit(X, y_reg),
    "classifier_rf": clf_rf.fit(X, y_clf),
    "classifier_log":clf_log.fit(X, y_clf)
}

# ---------- 7) Salvando artefatos no S3 ----------
ts = time_stamp()
s3 = boto3.client("s3")

for name, mdl in final_models.items():
    # Salva localmente primeiro
    local_path = ARTIFACTS_DIR / f"{name}_{ts}.joblib"
    joblib.dump(mdl, local_path, compress=("xz", 3))
    
    # Upload para S3
    s3_key = f"models/{name}_{ts}.joblib"
    s3.upload_file(str(local_path), BUCKET, s3_key)
    print(f"✅ Modelo salvo: {s3_key}")

# Salva arquivo de controle
latest_content = f"models/regressor_rf_{ts}.joblib\n{ts}\n5"
s3.put_object(Bucket=BUCKET, Key="models/latest_models.txt", Body=latest_content)
print(f"📋 Controle atualizado: models/latest_models.txt")

print("🎉 Treinamento concluído com sucesso!")