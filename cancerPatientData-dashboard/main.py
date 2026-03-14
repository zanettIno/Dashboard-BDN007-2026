import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os
from pathlib import Path


# LOAD DOS DADOS (via csv)
# ==================================================================

@st.cache_data
def load_dataset():
    # Tentar encontrar o arquivo em múltiplas localizações
    possible_paths = [
        "cancer_patient_data.csv",
        "./cancer_patient_data.csv",
        os.path.join(os.path.dirname(__file__), "cancer_patient_data.csv"),
        os.path.expanduser("~/Downloads/cancer_patient_data.csv"),
        os.path.expanduser("~/Desktop/cancer_patient_data.csv"),
    ]

    # Procurar o arquivo
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            st.success(f"✅ Arquivo carregado de: {csv_path}")
            break

    if csv_path is None:
        st.error(" Arquivo 'cancer_patient_data.csv' não encontrado!")
        st.info(" Coloque o arquivo em uma destas localizações:")
        for path in possible_paths:
            st.code(path)
        st.stop()

    data = pd.read_csv(csv_path)
    return data


dados = load_dataset()

# HEADER DO DASHBOARD
# ==================================================================

st.set_page_config(
    page_title="Dashboard Oncologia",
    page_icon="🏥",
    layout="wide")

st.title("🏥 Dashboard de Análise Oncológica")
st.markdown(
    "Sistema de análise clínica e epidemiológica de pacientes oncológicos. "
    "Monitore distribuição de casos, características de tumores, tipos de tratamento "
    "e outcomes clínicos de forma integrada.")

st.divider()

# FILTROS LATERAIS
# ==================================================================

st.sidebar.header("🔎 Filtros")

todos_tipos = sorted(dados["tumortype"].dropna().unique().tolist())
seletor_tipo = st.sidebar.multiselect(
    label="Selecione o tipo de tumor",
    options=todos_tipos,
    default=todos_tipos)

todos_estagios = sorted(dados["cancerstage"].dropna().unique().tolist())
seletor_estagio = st.sidebar.multiselect(
    label="Estágio do Câncer",
    options=todos_estagios,
    default=todos_estagios)

todos_tratamentos = sorted(dados["treatmenttype"].dropna().unique().tolist())
seletor_tratamento = st.sidebar.multiselect(
    label="Tipo de Tratamento",
    options=todos_tratamentos,
    default=[])

todas_provincias = sorted(dados["province"].dropna().unique().tolist())
seletor_provincia = st.sidebar.multiselect(
    label="Província/Região",
    options=todas_provincias,
    default=todas_provincias)

apenas_metastase = st.sidebar.toggle("Apenas com Metástase", value=False)

if not seletor_tipo:
    st.warning("Selecione pelo menos 1 tipo de tumor")
    st.stop()

# COMPUTACAO DOS DADOS (ativacao via .compute() seguindo filtros)
# ==================================================================

data_filtrada = dados[dados["tumortype"].isin(seletor_tipo)]
data_filtrada = data_filtrada[data_filtrada["cancerstage"].isin(seletor_estagio)]
data_filtrada = data_filtrada[data_filtrada["province"].isin(seletor_provincia)]

# optional
if seletor_tratamento:
    data_filtrada = data_filtrada[data_filtrada["treatmenttype"].isin(seletor_tratamento)]

# optional
if apenas_metastase:
    data_filtrada = data_filtrada[data_filtrada["metastasis"] == "Yes"]

with st.spinner("Gerando dashboard"):
    df = data_filtrada

    total_pacientes = len(df)
    media_idade = df["age"].mean()
    media_tamanho_tumor = df["tumorsize"].mean()
    qtd_metastase = (df["metastasis"] == "Yes").sum()
    taxa_sobrevivencia = (df["survivalstatus"] == "Alive").sum() / total_pacientes * 100 if total_pacientes > 0 else 0
    media_sessoes_quimio = df["chemotherapysessions"].mean()

# PRIMEIROS DADOS FILTRADOS EM NUMEROS
# ==================================================================

st.subheader("📈Indicadores Gerais")

k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric("👥 Total de Pacientes", f"{total_pacientes}")
k2.metric("📊 Taxa Sobrevivência", f"{taxa_sobrevivencia:.1f}%")
k3.metric("📏 Idade Média", f"{media_idade:.1f} anos")
k4.metric("🔬 Tamanho Tumor Médio", f"{media_tamanho_tumor:.1f} cm")
k5.metric("⚠️ Com Metástase", f"{int(qtd_metastase)}")
k6.metric("💊 Sessões Quimio Médias", f"{media_sessoes_quimio:.1f}")

st.divider()

# DISTRIBUICAO POR TIPO DE TUMOR
# ==================================================================

st.subheader("📈 Distribuição por Tipo de Tumor")

col1, col2 = st.columns(2)

with col1:
    contagem_tipo = (
        df.groupby("tumortype")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Quantidade", ascending=False)
    )

    fig_tipo = px.bar(
        contagem_tipo,
        x="tumortype", y="Quantidade",
        color="tumortype",
        title="Quantidade de Pacientes por Tipo de Tumor",
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Vivid,
        labels={"tumortype": "Tipo de Tumor", "Quantidade": "Número de Pacientes"}
    )
    fig_tipo.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_tipo, use_container_width=True)

with col2:
    taxa_sobrev_por_tipo = (
        df.groupby("tumortype")
        .apply(lambda x: (x["survivalstatus"] == "Alive").sum() / len(x) * 100)
        .reset_index(name="Taxa Sobrevivência (%)")
        .rename(columns={0: "tumortype"})
    )
    taxa_sobrev_por_tipo.columns = ["tumortype", "Taxa Sobrevivência (%)"]
    taxa_sobrev_por_tipo = taxa_sobrev_por_tipo.sort_values("Taxa Sobrevivência (%)", ascending=False)

    fig_sobrev = px.bar(
        taxa_sobrev_por_tipo,
        x="tumortype", y="Taxa Sobrevivência (%)",
        color="Taxa Sobrevivência (%)",
        title="Taxa de Sobrevivência por Tipo de Tumor",
        color_continuous_scale="RdYlGn",
        text_auto=".1f",
        labels={"tumortype": "Tipo de Tumor"}
    )
    fig_sobrev.update_layout(plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
    st.plotly_chart(fig_sobrev, use_container_width=True)

st.divider()

# GRAFICO DE DISPERSAO (Idade vs Tamanho do Tumor)
# ==================================================================

st.subheader("⚕️ Comparações Clínicas")

col3, = st.columns(1)

numeric_cols = ["age", "tumorsize", "chemotherapysessions", "radiationsessions", "followupmonths"]
col_labels = {
    "age": "Idade (anos)",
    "tumorsize": "Tamanho Tumor (cm)",
    "chemotherapysessions": "Sessões Quimio",
    "radiationsessions": "Sessões Radiação",
    "followupmonths": "Meses de Acompanhamento"
}

eixo_x = st.selectbox("Eixo X", options=numeric_cols, index=0, format_func=lambda x: col_labels[x])
eixo_y = st.selectbox("Eixo Y", options=numeric_cols, index=1, format_func=lambda x: col_labels[x])

with col3:
    fig_scatter = px.scatter(
        df,
        x=eixo_x, y=eixo_y,
        color="tumortype",
        hover_name="patientid",
        hover_data=["age", "tumorsize", "survivalstatus", "metastasis"],
        title=f"{col_labels[eixo_x]} vs {col_labels[eixo_y]}",
        opacity=0.7,
        color_discrete_sequence=px.colors.qualitative.Vivid,
        labels={eixo_x: col_labels[eixo_x], eixo_y: col_labels[eixo_y], "tumortype": "Tipo Tumor"}
    )
    fig_scatter.update_layout(plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# GRAFICO DE RADAR (Perfil Médio de Tratamento)
# ==================================================================

st.subheader("🕸️ Perfil Médio de Tratamento")

# Calculate mean of each treatment stat
stat_cols = ["age", "tumorsize", "chemotherapysessions", "radiationsessions", "followupmonths"]

# Normalize values para melhor visualização
df_temp = df[stat_cols].copy()
df_normalized = pd.DataFrame()
for col in stat_cols:
    max_val = df_temp[col].max()
    df_normalized[col] = (df_temp[col] / max_val * 100) if max_val > 0 else 0

medias_stats = df_normalized[stat_cols].mean().reset_index()
medias_stats.columns = ["Metrica", "Valor Normalizado (%)"]
medias_stats["Metrica"] = medias_stats["Metrica"].map(col_labels)

fig_radar = px.line_polar(
    medias_stats,
    r="Valor Normalizado (%)",
    theta="Metrica",
    line_close=True,
    title="Perfil Médio Normalizado (Pacientes Filtrados)",
    color_discrete_sequence=["#FF6B6B"],
)
fig_radar.update_traces(fill="toself", fillcolor="rgba(255,107,107,0.3)")
fig_radar.update_layout(plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# DISTRIBUICAO POR ESTAGIO E STATUS DE SOBREVIVENCIA
# ==================================================================

st.subheader("📊 Distribuição por Estágio e Resultado")

col4, col5 = st.columns(2)

with col4:
    dist_estagio = (
        df.groupby("cancerstage")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("cancerstage")
    )

    fig_estagio = px.bar(
        dist_estagio,
        x="cancerstage", y="Quantidade",
        color="cancerstage",
        title="Distribuição por Estágio do Câncer",
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"cancerstage": "Estágio", "Quantidade": "Número de Pacientes"}
    )
    fig_estagio.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_estagio, use_container_width=True)

with col5:
    dist_sobrevivencia = (
        df.groupby("survivalstatus")
        .size()
        .reset_index(name="Quantidade")
    )

    fig_pie = px.pie(
        dist_sobrevivencia,
        names="survivalstatus",
        values="Quantidade",
        title="Status de Sobrevivência",
        hole=0.3,
        color_discrete_sequence=px.colors.qualitative.Pastel,
        labels={"survivalstatus": "Status"}
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# TABELA DE PACIENTES CRÍTICOS (Maior Tamanho de Tumor + Metástase + Estágio Avançado)
# =============================================================================

st.subheader("🚨 Pacientes com Perfil de Maior Risco Clínico")

pacientes_risco = (
    df[(df["tumorsize"] > df["tumorsize"].quantile(0.75)) |
       (df["metastasis"] == "Yes") |
       (df["cancerstage"].isin(["III", "IV"]))]
    [["patientid", "age", "gender", "tumortype", "cancerstage", "tumorsize",
      "metastasis", "treatmenttype", "survivalstatus", "followupmonths"]]
    .sort_values("tumorsize", ascending=False)
    .reset_index(drop=True)
)
pacientes_risco.index += 1

st.dataframe(pacientes_risco.head(15), use_container_width=True)

st.divider()

# ANALISE POR TIPO DE TRATAMENTO
# ==================================================================

st.subheader("💊 Análise por Tipo de Tratamento")

col6, col7 = st.columns(2)

with col6:
    dist_tratamento = (
        df.groupby("treatmenttype")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Quantidade", ascending=False)
    )

    fig_tratamento = px.bar(
        dist_tratamento,
        x="treatmenttype", y="Quantidade",
        color="treatmenttype",
        title="Distribuição por Tipo de Tratamento",
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Dark2,
        labels={"treatmenttype": "Tratamento", "Quantidade": "Número de Pacientes"}
    )
    fig_tratamento.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_tratamento, use_container_width=True)

with col7:
    sobrev_tratamento = (
        df.groupby("treatmenttype")
        .apply(lambda x: (x["survivalstatus"] == "Alive").sum() / len(x) * 100)
        .reset_index(name="Taxa Sobrevivência (%)")
    )
    sobrev_tratamento.columns = ["treatmenttype", "Taxa Sobrevivência (%)"]
    sobrev_tratamento = sobrev_tratamento.sort_values("Taxa Sobrevivência (%)", ascending=False)

    fig_sobrev_trat = px.bar(
        sobrev_tratamento,
        x="treatmenttype", y="Taxa Sobrevivência (%)",
        color="Taxa Sobrevivência (%)",
        title="Taxa de Sobrevivência por Tratamento",
        color_continuous_scale="Viridis",
        text_auto=".1f",
        labels={"treatmenttype": "Tratamento"}
    )
    fig_sobrev_trat.update_layout(plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
    st.plotly_chart(fig_sobrev_trat, use_container_width=True)

st.divider()