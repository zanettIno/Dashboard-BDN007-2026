import dask.dataframe as dd
import pandas as pd
import streamlit as st

def load_dataset_lazy():
    """
    Carrega datasets de oncologia mantendo dados grandes em formato Dask (lazy).
    Retorna Dask DataFrames para datasets grandes e Pandas para pequenos.
    """

    # Datasets PEQUENOS - carregar direto em pandas
    candiSentimentos = dd.read_csv("candiSentimentos.csv").compute()
    candiSintomas = dd.read_csv("candiSintomas.csv").compute()
    datasetSerio = dd.read_csv("dataSeria.csv").compute()
    datasetNoticias = dd.read_csv("noticiasCancer.csv").compute()
    datasetSentimentos2 = dd.read_csv(
        "sentimentosOncologia.csv",
        sep=";",
        encoding="utf-8-sig",
        dtype={'none': 'object'}
    ).compute()
    datasetSobrevivencia = dd.read_csv("sobrevivenciaCancer.csv").compute()
    datasetTempoTratamento = dd.read_csv(
        "tempoP_inicioTratamento.csv",
        encoding="latin-1"
    ).compute()

    # Dataset GRANDE - manter em Dask (lazy)
    datasetSUS = dd.read_csv(
        "datasetSUS.csv",
        dtype={
            'ANOMES_TRA': 'float64',
            'CNES_TRAT': 'float64',
            'MUN_TRATAM': 'float64',
            'UF_TRATAM': 'float64',
        },
        blocksize="64MB"  # Processar em blocos de 64MB
    )

    return (
        candiSentimentos,
        candiSintomas,
        datasetSerio,
        datasetSUS,  # Retorna Dask DataFrame
        datasetNoticias,
        datasetSentimentos2,
        datasetSobrevivencia,
        datasetTempoTratamento
    )


@st.cache_data
def load_dataset_eager():
    """
    Versão não-lazy (eager) - carrega tudo em memória.
    Use apenas para datasets pequenos ou quando tiver memória suficiente.
    """

    candiSentimentos = dd.read_csv("candiSentimentos.csv").compute()
    candiSintomas = dd.read_csv("candiSintomas.csv").compute()
    datasetSerio = dd.read_csv("dataSeria.csv").compute()

    datasetSUS = dd.read_csv(
        "datasetSUS.csv",
        dtype={
            'ANOMES_TRA': 'float64',
            'CNES_TRAT': 'float64',
            'MUN_TRATAM': 'float64',
            'UF_TRATAM': 'float64',
        }
    ).compute()

    datasetNoticias = dd.read_csv("noticiasCancer.csv").compute()
    datasetSentimentos2 = dd.read_csv(
        "sentimentosOncologia.csv",
        sep=";",
        encoding="utf-8-sig",
        dtype={'none': 'object'}
    ).compute()
    datasetSobrevivencia = dd.read_csv("sobrevivenciaCancer.csv").compute()
    datasetTempoTratamento = dd.read_csv(
        "tempoP_inicioTratamento.csv",
        encoding="latin-1"
    ).compute()

    return (
        candiSentimentos,
        candiSintomas,
        datasetSerio,
        datasetSUS,
        datasetNoticias,
        datasetSentimentos2,
        datasetSobrevivencia,
        datasetTempoTratamento
    )
