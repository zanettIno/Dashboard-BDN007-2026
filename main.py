import dask.dataframe as dd
import pandas as pd
import numpy as np
import time
import streamlit as st
import plotly.express as px

# LOAD DOS DADOS (via csv; de forma lazy, somente plano de acao)
# ==================================================================

@st.cache_resource
def load_dataset():
    data = dd.read_csv("Pokemon.csv")
    return data

dados = load_dataset()

# HEADER DO DASHBOARD
# ==================================================================

st.set_page_config(
    page_title="Dashboard Poggers",
    page_icon="👻",
    layout="wide")

st.title("👻 Dashboard teste de Pokemon")
st.markdown(
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, " \
    "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua")

st.divider()

# FILTROS LATERAIS
# ==================================================================

st.sidebar.header("🔎 Filtros")

todos_tiposUM = sorted(dados["Type 1"].dropna().unique().compute().tolist())
seletor_tipoUM = st.sidebar.multiselect(
    label="Selecione o primeiro tipo",
    options=todos_tiposUM,
    default=todos_tiposUM)

todos_tiposDOIS = sorted(dados["Type 2"].dropna().unique().compute().tolist())
seletor_tipoDOIS = st.sidebar.multiselect(
    label="Selecione o segundo tipo",
    options=todos_tiposDOIS,
    default=[])

todas_geracoes = sorted(dados["Generation"].unique().compute().tolist())
seletor_geracao = st.sidebar.multiselect(
    label="Geração",
    options=todas_geracoes,
    default=todas_geracoes)

apenas_lendarios = st.sidebar.toggle("Apenas Lendários", value=False)

if not seletor_tipoUM:
    st.warning("⚠️ Selecione pelo menos 1 tipo")
    st.stop()  

# COMPUTACAO DOS DADOS (ativacao via .compute() seguindo filtros)
# ==================================================================

# Faz questao que os Pokemons tenham tipo e tenham geracao
data_filtrada = dados[dados["Type 1"].isin(seletor_tipoUM)]
data_filtrada = data_filtrada[data_filtrada["Generation"].isin(seletor_geracao)]

# optional
if seletor_tipoDOIS:
    data_filtrada = data_filtrada[data_filtrada["Type 2"].isin(seletor_tipoDOIS)]

# optional
if apenas_lendarios:
    data_filtrada = data_filtrada[data_filtrada["Legendary"] == True]

with st.spinner("Gerando dashboard"):
    df = data_filtrada.compute()

    total_pokemon = len(df)
    media_total_stats = df["Total"].mean()
    media_hp          = df["HP"].mean()
    media_ataque      = df["Attack"].mean()
    media_defesa      = df["Defense"].mean()
    qtd_lendarios     = df["Legendary"].sum()

# PRIMEIROS DADOS FILTRADOS EM NUMEROS
# ==================================================================

st.subheader("📈 Indicadores Gerais")

k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric("🐾 Total de Pokémon",    f"{total_pokemon}")
k2.metric("⭐ Lendários",           f"{int(qtd_lendarios)}")
k3.metric("💪 Média Total Stats",   f"{media_total_stats:.1f}")
k4.metric("❤️ Média HP",            f"{media_hp:.1f}")
k5.metric("⚔️ Média Ataque",        f"{media_ataque:.1f}")
k6.metric("🛡️ Média Defesa",        f"{media_defesa:.1f}")

st.divider()

# DISTRIBUICAO POR GRAFICOS DE BARRAS
# ==================================================================

st.subheader("📈 Distribuição por Tipo")

col1, col2 = st.columns(2)

with col1:
    
    contagem_tipo1 = (
        df.groupby("Type 1")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Quantidade", ascending=False)
    )

    fig_tipo1 = px.bar(
        contagem_tipo1,
        x="Type 1", y="Quantidade",
        color="Type 1",
        title="Quantidade de Pokémon por Tipo 1",
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig_tipo1.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_tipo1, use_container_width=True)

with col2:
    
    media_por_tipo = (
        df.groupby("Type 1")["Total"]
        .mean()
        .reset_index()
        .rename(columns={"Total": "Média Total"})
        .sort_values("Média Total", ascending=False)
    )
    
    fig_media = px.bar(
        media_por_tipo,
        x="Type 1", y="Média Total",
        color="Média Total",
        title="Média de Stats Totais por Tipo 1",
        color_continuous_scale="RdYlGn",
        text_auto=".1f",
    )
    fig_media.update_layout(plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
    st.plotly_chart(fig_media, use_container_width=True)

st.divider()

# GRAFICO DE DISPERSAO (maiores ataques e defesas espalhados)
# ==================================================================

st.subheader("⚔️ Comparacoes gerais de stats")

col3, = st.columns(1)

numeric_cols = ["HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed", "Total"]
eixo_x = st.selectbox("Eixo X", options=numeric_cols, index=1)  
eixo_y = st.selectbox("Eixo Y", options=numeric_cols, index=2)  

with col3:
    fig_scatter = px.scatter(
        df,
        x=eixo_x, y=eixo_y,
        color="Type 1",
        hover_name="Name",
        hover_data=["HP", "Total", "Legendary"],
        title="Ataque vs Defesa (por Tipo 1)",
        opacity=0.7,
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig_scatter.update_layout(plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# GRAFICO DE RADAS (jojo)
# ==================================================================

st.subheader("🕸️ Perfil Médio de Stats")

# Calculate mean of each stat column across filtered Pokémon
stat_cols = ["HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed"]
medias_stats = df[stat_cols].mean().reset_index()
medias_stats.columns = ["Stat", "Valor"]

fig_radar = px.line_polar(
    medias_stats,
    r="Valor",
    theta="Stat",
    line_close=True,
    title="Média de cada Stat (Pokémon filtrados)",
    color_discrete_sequence=["#FF6B6B"],
)
fig_radar.update_traces(fill="toself", fillcolor="rgba(255,107,107,0.3)")
fig_radar.update_layout(plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# TABELA DE TOP 10
# =============================================================================

st.subheader("🏆 Top 10 Pokémon por Total de Stats")

top10 = (
    df[["Name", "Type 1", "Type 2", "Total", "HP", "Attack", "Defense",
        "Sp. Atk", "Sp. Def", "Speed", "Generation", "Legendary"]]
    .sort_values("Total", ascending=False)
    .head(10)
    .reset_index(drop=True)
)
top10.index += 1  # start ranking at 1

st.dataframe(top10, use_container_width=True)

st.divider()