import dask.dataframe as dd
import pandas as pd
import streamlit as st
import requests

from load_kaggle import get_datasets_path

import os
DASHBOARD_API_URL = os.environ.get("DASHBOARD_API_URL", "")

def _fetch_candi_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    response = requests.get(f"{DASHBOARD_API_URL}/dashboard", timeout=30)
    response.raise_for_status()
    data = response.json()
    return pd.DataFrame(data["candiSentimentos"]), pd.DataFrame(data["candiSintomas"])


def load_dataset_lazy():
    paths = get_datasets_path()  

    candiSentimentos, candiSintomas = _fetch_candi_data()

    datasetSerio       = dd.read_csv(paths["dataSeria.csv"]).compute()
    datasetNoticias = dd.read_csv(
    paths["noticiasCancer.csv"],
    on_bad_lines='skip'   
).compute()
    datasetSentimentos2 = dd.read_csv(
        paths["sentimentosOncologia.csv"], sep=";", encoding="utf-8-sig", dtype={'none': 'object'}
    ).compute()
    datasetSobrevivencia   = dd.read_csv(paths["sobrevivenciaCancer.csv"]).compute()
    datasetTempoTratamento = dd.read_csv(
        paths["tempoP_inicioTratamento.csv"], encoding="latin-1"
    ).compute()

    datasetSUS = dd.read_csv(
        paths["datasetSUS.csv"],
        dtype={
            'ANOMES_TRA': 'float64', 'CNES_TRAT': 'float64',
            'MUN_TRATAM': 'float64', 'UF_TRATAM': 'float64',
        },
        blocksize="64MB"
    )

    return (
        candiSentimentos, candiSintomas, datasetSerio, datasetSUS,
        datasetNoticias, datasetSentimentos2, datasetSobrevivencia, datasetTempoTratamento
    )
