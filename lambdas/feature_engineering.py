import os, io, boto3, gzip, json, logging
import pandas as pd
import numpy as np
from datetime import datetime

s3 = boto3.client("s3")
BUCKET = "criptos-data"
RAW_KEY = "raw.csv"                                   # ajuste se mudar a pasta
FEAT_PREFIX = "features/"                             # saída

def lambda_handler(event, context):
    # 1. Lê raw.csv do S3 em memória
    obj = s3.get_object(Bucket=BUCKET, Key=RAW_KEY)
    df  = pd.read_csv(obj["Body"], sep="|", names=[
        "ativo", "data", "timestamp", "maximo", "minimo",
        "abertura", "fechamento", "volumefrom", "volumeto"
    ], skiprows=1, encoding="utf-8")

    # 2. Pré‑processo padrão (idêntico ao seu notebook)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    for c in ["maximo","minimo","abertura","fechamento","volumefrom","volumeto"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.drop(columns=["timestamp"]).sort_values(["ativo","data"]).reset_index(drop=True)

    # 3. Feature engineering (encapsule seu código em função p/ legibilidade)
    df = build_features(df)

    # 4. Grava em Parquet (mais compacto) no S3
    out_key = f"{FEAT_PREFIX}cripto_features_{datetime.utcnow():%Y%m%d}.parquet"
    buf     = io.BytesIO()
    df.to_parquet(buf, index=False)   # pyarrow
    buf.seek(0)
    s3.put_object(Bucket=BUCKET, Key=out_key, Body=buf.getvalue())

    # 5. Atualiza ponteiro “latest”
    s3.copy_object(
        Bucket=BUCKET,
        CopySource=f"{BUCKET}/{out_key}",
        Key=f"{FEAT_PREFIX}latest.parquet"
    )

    return {"status": "ok", "output": out_key}

def build_features(df):
    EPS = 1e-9

    # Ordenação para janelas, lags e cumulativos
    df = df.sort_values(['ativo','data']).reset_index(drop=True)

    # ---------------------------
    # Lags
    # ---------------------------
    df['fech_prev'] = df.groupby('ativo')['fechamento'].shift(1)
    df['abert_prev'] = df.groupby('ativo')['abertura'].shift(1)
    df['vol_prev']   = df.groupby('ativo')['volumefrom'].shift(1)

    # ---------------------------
    # Retornos
    # ---------------------------
    df['retorno_diario'] = (df['fechamento'] - df['fech_prev']) / df['fech_prev']

    # Retorno log robusto: diff do log com EPS e filtragem de valores não positivos
    log_fech = df.groupby('ativo')['fechamento'].transform(
        lambda s: np.where(s > 0, np.log(s + EPS), np.nan)
    )
    df['retorno_log'] = log_fech - log_fech.groupby(df['ativo']).shift(1)

    df['retorno_acumulado'] = df.groupby('ativo')['retorno_diario'].cumsum()

    # ---------------------------
    # Médias móveis e volatilidade simples
    # ---------------------------
    df['valor_mm_5']  = df.groupby('ativo')['fechamento'].transform(lambda s: s.rolling(5,  min_periods=1).mean())
    df['valor_mm_20'] = df.groupby('ativo')['fechamento'].transform(lambda s: s.rolling(20, min_periods=1).mean())

    df['volatilidade_5'] = df.groupby('ativo')['fechamento'].transform(lambda s: s.rolling(5, min_periods=2).std())

    df['abertura_mm_5']  = df.groupby('ativo')['abertura'].transform(lambda s: s.rolling(5,  min_periods=1).mean())
    df['abertura_mm_20'] = df.groupby('ativo')['abertura'].transform(lambda s: s.rolling(20, min_periods=1).mean())

    df['volume_mm_5']  = df.groupby('ativo')['volumefrom'].transform(lambda s: s.rolling(5,  min_periods=1).mean())
    df['volume_mm_20'] = df.groupby('ativo')['volumefrom'].transform(lambda s: s.rolling(20, min_periods=1).mean())

    # ---------------------------
    # Estatística robusta (mediana, MAD, IQR) e z-score robusto
    # ---------------------------
    def rolling_median(s, w):
        return s.rolling(w, min_periods=3).median()

    def rolling_mad(s, w):
        med = s.rolling(w, min_periods=3).median()
        return (s - med).abs().rolling(w, min_periods=3).median()

    def rolling_iqr(s, w):
        q75 = s.rolling(w, min_periods=5).quantile(0.75)
        q25 = s.rolling(w, min_periods=5).quantile(0.25)
        return q75 - q25

    df['mediana_20'] = df.groupby('ativo')['fechamento'].transform(lambda s: rolling_median(s, 20))
    df['mad_20']     = df.groupby('ativo')['fechamento'].transform(lambda s: rolling_mad(s, 20))
    df['iqr_20']     = df.groupby('ativo')['fechamento'].transform(lambda s: rolling_iqr(s, 20))

    den = 1.4826 * df['mad_20'].replace(0, np.nan)
    df['z_robusto_20'] = (df['fechamento'] - df['mediana_20']) / den

    # ---------------------------
    # Volatilidade de faixa (Parkinson) e ATR
    # ---------------------------
    # Evitar log de não-positivos
    df.loc[df['maximo'] <= 0, 'maximo'] = np.nan
    df.loc[df['minimo'] <= 0, 'minimo'] = np.nan

    k = 1.0 / (4.0 * np.log(2.0))
    df['hl_log2'] = np.log((df['maximo'] + EPS) / (df['minimo'] + EPS)) ** 2

    df['parkinson_10'] = df.groupby('ativo')['hl_log2'].transform(
        lambda s: (k * s).rolling(10, min_periods=5).mean()
    ) ** 0.5

    fech_prev = df.groupby('ativo')['fechamento'].shift(1)
    tr = pd.concat([
        (df['maximo'] - df['minimo']).abs(),
        (df['maximo'] - fech_prev).abs(),
        (df['minimo'] - fech_prev).abs()
    ], axis=1).max(axis=1)

    df['atr_14'] = tr.groupby(df['ativo']).transform(lambda s: s.rolling(14, min_periods=3).mean())

    # ---------------------------
    # Candle e posição no range
    # ---------------------------
    den_range = (df['maximo'] - df['minimo']).replace(0, np.nan)
    df['pos_no_range']    = (df['fechamento'] - df['minimo']) / den_range
    df['shadow_superior'] = df['maximo'] - df[['abertura','fechamento']].max(axis=1)
    df['shadow_inferior'] = df[['abertura','fechamento']].min(axis=1) - df['minimo']
    df['candle_corpo']    = (df['fechamento'] - df['abertura']).abs()

    dir_sign = np.sign(df['fechamento'] - df['abertura'])
    df['candle_direcao'] = np.select(
        [dir_sign > 0, dir_sign < 0, dir_sign == 0],
        ['bull', 'bear', 'doji'],
        default="nan"
    )

    # ---------------------------
    # Volume/surpresa
    # ---------------------------
    df['vol_pct_change']  = df.groupby('ativo')['volumefrom'].pct_change()

    vol_med20 = df.groupby('ativo')['volumefrom'].transform(lambda s: s.rolling(20, min_periods=3).median())
    vol_mad20 = df.groupby('ativo')['volumefrom'].transform(lambda s: (s - vol_med20).abs().rolling(20, min_periods=3).median())
    df['volume_z_rob_20'] = (df['volumefrom'] - vol_med20) / (1.4826 * vol_mad20.replace(0, np.nan))

    df['preco_medio_volume'] = df['volumeto'] / df['volumefrom']

    # ---------------------------
    # Drawdown
    # ---------------------------
    df['max_acum'] = df.groupby('ativo')['fechamento'].cummax()
    df['drawdown'] = (df['fechamento'] / df['max_acum']) - 1.0

    # ---------------------------
    # Temporais e categóricas
    # ---------------------------
    df['dia_semana'] = df['data'].dt.weekday
    df['mes']        = df['data'].dt.month

    comp_fech = np.sign(df['fechamento'] - df['fech_prev'])
    df['fechamento_categoria'] = np.select(
        [comp_fech > 0, comp_fech < 0, comp_fech == 0],
        ["acima", "abaixo", "igual"],
        default="nan"
    )

    comp_vol = np.sign(df['volumefrom'] - df['vol_prev'])
    df['volume_categoria'] = np.select(
        [comp_vol > 0, comp_vol < 0, comp_vol == 0],
        ["acima", "abaixo", "igual"],
        default="nan"
    )

    # ---------------------------
    # Limpeza final
    # ---------------------------
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    # Opcional: dropar linhas sem 'data' ou 'fechamento'
    # df = df.dropna(subset=['data','fechamento'])

    return df