import dask.dataframe as dd
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from load_datasets import load_dataset_lazy

# CONFIGURAÇÃO DE PÁGINA
# ==================================================================

st.set_page_config(
    page_title="Dashboard de Análise Oncológica - CANDI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CONSTANTES
# ==================================================================

TRANSPARENT_BG = "rgba(0,0,0,0)"
SAMPLE_SIZE = 50000  # Limite de amostras para datasets grandes

# LOAD DOS DADOS (Lazy - mantém em Dask até necessário)
# ==================================================================

@st.cache_resource
def get_lazy_datasets():
    """Carrega datasets mantendo formato Dask para eficiência"""
    return load_dataset_lazy()

with st.spinner("🔄 Carregando datasets (modo lazy)..."):
    (
        candiSentimentos,
        candiSintomas,
        datasetSerio,
        datasetSUS_dask,  # Mantido como Dask
        datasetNoticias,
        datasetSentimentos2,
        datasetSobrevivencia,
        datasetTempoTratamento
    ) = get_lazy_datasets()

# HEADER
# ==================================================================

st.title("🧬 Dashboard de Análise Oncológica - CANDI")
st.markdown(
    """
    Sistema de análise clínica e epidemiológica de pacientes oncológicos.
    Monitore distribuição de casos, características de tumores e outcomes clínicos.
    """
)
st.divider()

# SIDEBAR - FILTROS
# ==================================================================

st.sidebar.header("🔎 Filtros")

# Amostragem para performance
usar_amostra = st.sidebar.checkbox("Usar amostra do SUS (mais rápido)", value=True)
tamanho_amostra = st.sidebar.slider("Tamanho da amostra SUS", 1000, 100000, 10000, step=1000) if usar_amostra else None

# Filtros calculados de forma lazy
with st.spinner("Calculando filtros disponíveis..."):
    # Amostra para obter valores únicos rapidamente
    sample_sus = datasetSUS_dask.sample(frac=0.01, random_state=42)

    anos_disponiveis = sorted(sample_sus['ANO_DIAGN'].dropna().unique().compute())
    ufs_disponiveis = sorted(sample_sus['UF_RESID'].dropna().unique().compute())

seletor_ano = st.sidebar.multiselect(
    "Ano de Diagnóstico",
    options=anos_disponiveis,
    default=anos_disponiveis[-3:] if len(anos_disponiveis) >= 3 else anos_disponiveis
)

seletor_uf = st.sidebar.multiselect(
    "UF de Residência",
    options=ufs_disponiveis,
    default=[]
)

seletor_sexo = st.sidebar.multiselect(
    "Sexo",
    options=['M', 'F'],
    default=['M', 'F'],
    format_func=lambda x: 'Masculino' if x == 'M' else 'Feminino'
)

# Filtros Sobrevivência
tipos_tumor = sorted(datasetSobrevivencia['tumortype'].unique())
seletor_tumor = st.sidebar.multiselect(
    "Tipo de Tumor",
    options=tipos_tumor,
    default=tipos_tumor[:3] if len(tipos_tumor) > 3 else tipos_tumor
)

estagios = ['I', 'II', 'III', 'IV']
seletor_estagio = st.sidebar.multiselect(
    "Estágio",
    options=estagios,
    default=estagios
)

# APLICAR FILTROS (Lazy)
# ==================================================================

with st.spinner("Aplicando filtros..."):
    # Aplicar filtros no SUS de forma lazy
    if usar_amostra:
        # Usar amostra aleatória para performance
        datasetSUS_amostra = datasetSUS_dask.sample(frac=tamanho_amostra/datasetSUS_dask.shape[0].compute(), random_state=42)
    else:
        datasetSUS_amostra = datasetSUS_dask

    # Aplicar filtros
    mask_sus = datasetSUS_amostra['ANO_DIAGN'].isin(seletor_ano) if seletor_ano else True
    if seletor_sexo:
        mask_sus = mask_sus & datasetSUS_amostra['SEXO'].isin(seletor_sexo)
    if seletor_uf:
        mask_sus = mask_sus & datasetSUS_amostra['UF_RESID'].isin(seletor_uf)

    datasetSUS_filtrado = datasetSUS_amostra[mask_sus]

    # Filtrar Sobrevivência (já é pandas, é pequeno)
    filtros_sobrev = datasetSobrevivencia[
        (datasetSobrevivencia['tumortype'].isin(seletor_tumor) if seletor_tumor else True) &
        (datasetSobrevivencia['cancerstage'].isin(seletor_estagio) if seletor_estagio else True)
    ]

# INDICADORES
# ==================================================================

with st.spinner("Calculando indicadores..."):
    # Calcular total do SUS (lazy -> compute)
    total_sus = datasetSUS_filtrado.shape[0].compute()

    # Calcular metricas de sobrevivencia (ja eh pandas)
    total_sobrev = len(filtros_sobrev)
    taxa_sobrev = (filtros_sobrev['survivalstatus'] == 'Alive').mean() * 100 if total_sobrev > 0 else 0

    # Cache com valores simples (hashaveis)
    indicadores_sus = {"total": int(total_sus)}
    indicadores_sobrev = {"total": total_sobrev, "taxa_sobrevivencia": taxa_sobrev}

st.subheader("📊 Indicadores Gerais")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("👥 Pacientes (SUS)", f"{indicadores_sus['total']:,}")
with col2:
    st.metric("💚 Taxa Sobrev.", f"{indicadores_sobrev['taxa_sobrevivencia']:.1f}%")
with col3:
    st.metric("📅 Sentimentos", f"{len(candiSentimentos):,}")
with col4:
    st.metric("📝 Sintomas", f"{len(candiSintomas):,}")
with col5:
    st.metric("📰 Artigos", f"{len(datasetNoticias):,}")
with col6:
    st.metric("🧪 Amostras Tumorais", f"{len(datasetSerio):,}")

st.divider()

# ANÁLISE EPIDEMIOLÓGICA
# ==================================================================

st.subheader("🏥 Análise Epidemiológica")

col1, col2 = st.columns(2)

with col1:
    with st.spinner("Gerando gráfico de sexo..."):
        # Agregação lazy
        sexo_counts = datasetSUS_filtrado.groupby('SEXO').size().compute().reset_index()
        sexo_counts.columns = ['Sexo', 'Quantidade']
        sexo_counts['Sexo'] = sexo_counts['Sexo'].map({'M': 'Masculino', 'F': 'Feminino'})

        fig = px.pie(sexo_counts, values='Quantidade', names='Sexo',
                    title='Distribuição por Sexo',
                    color_discrete_sequence=['#4A90D9', '#E74C3C'])
        st.plotly_chart(fig, use_container_width=True)

with col2:
    with st.spinner("Gerando gráfico por ano..."):
        # Agregação lazy - limitar a top 10 anos
        ano_counts = (datasetSUS_filtrado.groupby('ANO_DIAGN').size()
                     .compute().reset_index().sort_values('ANO_DIAGN'))
        ano_counts.columns = ['Ano', 'Quantidade']

        fig = px.bar(ano_counts.tail(10), x='Ano', y='Quantidade',
                    title='Casos por Ano (últimos 10)',
                    color='Quantidade', color_continuous_scale='Blues')
        fig.update_layout(plot_bgcolor=TRANSPARENT_BG)
        st.plotly_chart(fig, use_container_width=True)

# Casos por UF (Top 10)
st.subheader("🗺️ Distribuição Geográfica (Top 10 UFs)")

with st.spinner("Calculando distribuição geográfica..."):
    uf_counts = (datasetSUS_filtrado.groupby('UF_RESID').size()
                .compute().reset_index().sort_values(0, ascending=False).head(10))
    uf_counts.columns = ['UF', 'Quantidade']

    fig = px.bar(uf_counts, x='UF', y='Quantidade',
                title='Top 10 UFs com mais casos',
                color='Quantidade', color_continuous_scale='Viridis')
    fig.update_layout(plot_bgcolor=TRANSPARENT_BG)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ANÁLISE DE SOBREVIVÊNCIA
# ==================================================================

st.subheader("💚 Análise de Sobrevivência")

col3, col4 = st.columns(2)

with col3:
    survival_by_tumor = (filtros_sobrev.groupby('tumortype')['survivalstatus']
                        .apply(lambda x: (x == 'Alive').sum() / len(x) * 100)
                        .reset_index())
    survival_by_tumor.columns = ['Tipo', 'Taxa (%)']

    fig = px.bar(survival_by_tumor, x='Tipo', y='Taxa (%)',
                title='Taxa de Sobrevivência por Tumor',
                color='Taxa (%)', color_continuous_scale='RdYlGn')
    fig.update_layout(plot_bgcolor=TRANSPARENT_BG)
    st.plotly_chart(fig, use_container_width=True)

with col4:
    estagio_counts = filtros_sobrev['cancerstage'].value_counts().reset_index()
    estagio_counts.columns = ['Estágio', 'Quantidade']

    fig = px.pie(estagio_counts, values='Quantidade', names='Estágio',
                title='Distribuição por Estágio',
                color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig, use_container_width=True)

# Scatter plot (limitado a 1000 pontos)
st.subheader("📈 Tamanho do Tumor vs Acompanhamento")

sample_sobrev = filtros_sobrev.sample(min(1000, len(filtros_sobrev)), random_state=42) if len(filtros_sobrev) > 1000 else filtros_sobrev

fig = px.scatter(sample_sobrev, x='tumorsize', y='followupmonths',
                color='survivalstatus', symbol='cancerstage',
                title=f'Amostra de {len(sample_sobrev)} pacientes',
                color_discrete_map={'Alive': '#2ECC71', 'Deceased': '#E74C3C'})
fig.update_layout(plot_bgcolor=TRANSPARENT_BG)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# CARACTERÍSTICAS DO TUMOR
# ==================================================================

st.subheader("🔬 Características dos Tumores (Wisconsin)")

col5, col6 = st.columns(2)

with col5:
    diag_counts = datasetSerio['diagnosis'].value_counts().reset_index()
    diag_counts.columns = ['Diag', 'Quantidade']
    diag_counts['Diagnóstico'] = diag_counts['Diag'].map({'M': 'Maligno', 'B': 'Benigno'})

    fig = px.pie(diag_counts, values='Quantidade', names='Diagnóstico',
                title='Diagnósticos',
                color='Diagnóstico',
                color_discrete_map={'Maligno': '#E74C3C', 'Benigno': '#2ECC71'})
    st.plotly_chart(fig, use_container_width=True)

with col6:
    fig = px.box(datasetSerio, x='diagnosis', y='radius_mean',
                color='diagnosis',
                title='Raio Médio por Diagnóstico',
                labels={'diagnosis': 'Tipo', 'radius_mean': 'Raio (mm)'},
                color_discrete_map={'M': '#E74C3C', 'B': '#2ECC71'})
    fig.update_layout(plot_bgcolor=TRANSPARENT_BG, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# Heatmap de correlação (amostra se necessário)
st.subheader("🌡️ Correlação entre Características")

features = ['radius_mean', 'texture_mean', 'perimeter_mean', 'area_mean',
            'smoothness_mean', 'compactness_mean', 'concavity_mean']
corr_matrix = datasetSerio[features].corr()

fig = px.imshow(corr_matrix, text_auto='.1f', aspect='auto',
                color_continuous_scale='RdBu_r')
st.plotly_chart(fig, use_container_width=True)

st.divider()

# SENTIMENTOS E SINTOMAS
# ==================================================================

st.subheader("😊 Sentimentos e Sintomas (CANDI)")

col7, col8 = st.columns(2)

with col7:
    happiness_counts = candiSentimentos['happiness'].value_counts().sort_index().reset_index()
    happiness_counts.columns = ['Nível', 'Quantidade']

    fig = px.bar(happiness_counts, x='Nível', y='Quantidade',
                title='Nível de Felicidade',
                color='Quantidade', color_continuous_scale='RdYlGn')
    fig.update_layout(plot_bgcolor=TRANSPARENT_BG)
    st.plotly_chart(fig, use_container_width=True)

with col8:
    # Usar a coluna 'data' já convertida no cross-dataset section
    if 'data' not in candiSentimentos.columns:
        candiSentimentos['data'] = pd.to_datetime(candiSentimentos['created_at'], errors='coerce')
    candiSentimentos['data_date'] = candiSentimentos['data'].dt.date
    timeline = candiSentimentos.groupby('data_date')['happiness'].mean().reset_index()

    fig = px.line(timeline, x='data_date', y='happiness',
                 title='Evolução do Sentimento', markers=True)
    fig.update_layout(plot_bgcolor=TRANSPARENT_BG)
    st.plotly_chart(fig, use_container_width=True)

# Top sintomas
st.subheader("🩺 Top Sintomas")

sintomas_lista = (candiSintomas['description'].str.lower()
                 .str.split(r'[,;]').explode().str.strip())
sintomas_counts = sintomas_lista.value_counts().head(10).reset_index()
sintomas_counts.columns = ['Sintoma', 'Frequência']

fig = px.bar(sintomas_counts, x='Frequência', y='Sintoma',
            orientation='h', title='Top 10 Sintomas',
            color='Frequência', color_continuous_scale='Reds')
fig.update_layout(plot_bgcolor=TRANSPARENT_BG)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# CROSS-DATASET ANALYSIS
# ==================================================================

st.subheader("🔗 Análise Cruzada de Datasets")

st.markdown("Comparação entre diferentes fontes de dados para identificar padrões.")

col_cross1, col_cross2 = st.columns(2)

with col_cross1:
    st.markdown("**Distribuição Etária: CANDI vs Sobrevivência**")

    # Idade no dataset CANDI (calculada aproximada pelo perfil - simplificado)
    candiSentimentos['data'] = pd.to_datetime(candiSentimentos['created_at'], errors='coerce')
    idade_candi = candiSentimentos['data'].dt.year - 2020  # Proxy simplificado
    idade_candi = idade_candi.clip(18, 80)  # Limitar a faixa etária razoável

    # Idade no dataset Sobrevivência
    idade_sobrev = filtros_sobrev['age'].dropna()

    # Criar bins de idade
    bins = [0, 30, 40, 50, 60, 70, 100]
    labels = ['<30', '30-40', '40-50', '50-60', '60-70', '70+']

    candi_bins = pd.cut(idade_candi, bins=bins, labels=labels).value_counts().sort_index()
    sobrev_bins = pd.cut(idade_sobrev, bins=bins, labels=labels).value_counts().sort_index()

    # Normalizar para percentual
    candi_pct = (candi_bins / candi_bins.sum() * 100).reset_index()
    candi_pct.columns = ['Faixa', 'Percentual']
    candi_pct['Dataset'] = 'CANDI (Sentimentos)'

    sobrev_pct = (sobrev_bins / sobrev_bins.sum() * 100).reset_index()
    sobrev_pct.columns = ['Faixa', 'Percentual']
    sobrev_pct['Dataset'] = 'Sobrevivência'

    cross_data = pd.concat([candi_pct, sobrev_pct])

    fig = px.bar(cross_data, x='Faixa', y='Percentual', color='Dataset',
                barmode='group',
                title='Distribuição Etária por Dataset',
                color_discrete_sequence=['#4A90D9', '#E74C3C'])
    fig.update_layout(plot_bgcolor=TRANSPARENT_BG)
    st.plotly_chart(fig, use_container_width=True)

with col_cross2:
    st.markdown("**Felícidade CANDI vs Estágio do Câncer**")

    # Agregar sentimentos por mês
    candiSentimentos['mes'] = candiSentimentos['data'].dt.to_period('M')
    sentimento_mensal = candiSentimentos.groupby('mes')['happiness'].mean().reset_index()
    sentimento_mensal['mes_str'] = sentimento_mensal['mes'].astype(str)

    # Distribuição de estágios no dataset Sobrevivência
    estagio_dist = filtros_sobrev['cancerstage'].value_counts(normalize=True).reset_index()
    estagio_dist.columns = ['Estágio', 'Proporção']
    estagio_dist['Proporção'] *= 100

    # Criar duplo eixo (subplots)
    from plotly.subplots import make_subplots

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Barra para estágios
    fig.add_trace(
        go.Bar(x=estagio_dist['Estágio'], y=estagio_dist['Proporção'],
               name='% Estágios (Sobrevivência)', marker_color='#E74C3C'),
        secondary_y=False
    )

    # Linha para felicidade (média geral como referência)
    felicidade_media = candiSentimentos['happiness'].mean()
    fig.add_trace(
        go.Scatter(x=estagio_dist['Estágio'],
                    y=[felicidade_media] * len(estagio_dist),
                    name=f'Felicidade Média CANDI ({felicidade_media:.1f})',
                    mode='lines+markers',
                    line=dict(color='#2ECC71', width=3)),
        secondary_y=True
    )

    fig.update_layout(
        title_text="Estágio do Câncer vs Felicidade Média",
        plot_bgcolor=TRANSPARENT_BG
    )
    fig.update_yaxes(title_text="% Pacientes por Estágio", secondary_y=False)
    fig.update_yaxes(title_text="Nível de Felicidade", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

# Segundo gráfico cross-dataset: Comparação de severidade
st.markdown("**🔬 Severidade do Tumor: Dataset Wisconsin vs Sobrevivência**")

# Dataset Wisconsin - Radius (proxy para severidade)
severidade_wisconsin = datasetSerio.copy()
severidade_wisconsin['Severidade'] = pd.cut(
    severidade_wisconsin['radius_mean'],
    bins=[0, 12, 16, 20, 50],
    labels=['Baixa', 'Média', 'Alta', 'Muito Alta']
)

# Contagem por severidade
sev_wisc = severidade_wisconsin['Severidade'].value_counts().reset_index()
sev_wisc.columns = ['Severidade', 'Contagem']
sev_wisc['Dataset'] = 'Wisconsin (Tumor)'

# Dataset Sobrevivência - Tumor size como proxy
severidade_sobrev = filtros_sobrev.copy()
severidade_sobrev['Severidade'] = pd.cut(
    severidade_sobrev['tumorsize'],
    bins=[0, 6, 8, 10, 20],
    labels=['Baixa', 'Média', 'Alta', 'Muito Alta']
)

sev_sobrev = severidade_sobrev['Severidade'].value_counts().reset_index()
sev_sobrev.columns = ['Severidade', 'Contagem']
sev_sobrev['Dataset'] = 'Sobrevivência'

# Combinar
cross_sev = pd.concat([sev_wisc, sev_sobrev])

fig = px.bar(cross_sev, x='Severidade', y='Contagem', color='Dataset',
            barmode='group',
            title='Distribuição de Severidade Tumoral por Dataset',
            color_discrete_sequence=['#9B59B6', '#F39C12'])
fig.update_layout(plot_bgcolor=TRANSPARENT_BG)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# TEMPO DE TRATAMENTO (SEÇÃO OTIMIZADA)
# ==================================================================

st.subheader("⏱️ Tempo para Início do Tratamento")

# Usar amostra pequena para evitar freeze
with st.spinner("Carregando dados de tratamento (amostra)..."):
    # Calcular idade apenas para amostra
    sample_tempo = datasetSUS_filtrado.sample(frac=0.05, random_state=42) if len(datasetSUS_filtrado) > 10000 else datasetSUS_filtrado

    if hasattr(sample_tempo, 'compute'):
        sample_tempo = sample_tempo.compute()

    if len(sample_tempo) > 0 and 'TEMPO_TRAT' in sample_tempo.columns:
        sample_tempo['DT_NASC'] = pd.to_datetime(sample_tempo['DT_NASC'], errors='coerce')
        sample_tempo['DT_DIAG'] = pd.to_datetime(sample_tempo['DT_DIAG'], errors='coerce')
        sample_tempo['IDADE'] = (sample_tempo['DT_DIAG'] - sample_tempo['DT_NASC']).dt.days / 365.25

        # Filtrar valores válidos
        filtered_data = sample_tempo[
            (sample_tempo['TEMPO_TRAT'].notna()) &
            (sample_tempo['TEMPO_TRAT'] >= 0) &
            (sample_tempo['TEMPO_TRAT'] < 365) &  # Remove outliers
            (sample_tempo['IDADE'].notna()) &
            (sample_tempo['IDADE'] > 0) &
            (sample_tempo['IDADE'] < 120)
        ]

        # Amostrar apenas se houver mais dados que o tamanho desejado
        if len(filtered_data) > 5000:
            plot_data = filtered_data.sample(5000, random_state=42)
        else:
            plot_data = filtered_data

        if len(plot_data) > 0:
            fig = px.scatter(plot_data, x='IDADE', y='TEMPO_TRAT',
                           title=f'Idade vs Tempo de Tratamento (Amostra: {len(plot_data)} pacientes)',
                           labels={'IDADE': 'Idade (anos)', 'TEMPO_TRAT': 'Dias até Tratamento'},
                           opacity=0.5)
            fig.update_layout(plot_bgcolor=TRANSPARENT_BG)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para visualização.")
    else:
        st.info("Dados de tempo de tratamento não disponíveis com os filtros atuais.")

# Dados do CSV de tempo de tratamento por região
st.subheader("📍 Tempo de Tratamento por Região")

if not datasetTempoTratamento.empty:
    # Processar dados do CSV de tempo por região
    try:
        regioes = []
        for _, row in datasetTempoTratamento.iterrows():
            if ';' in str(row.iloc[0]):
                partes = str(row.iloc[0]).split(';')
                regioes.append({
                    'Região': partes[0],
                    'Dados': row.iloc[0]
                })

        if regioes:
            st.dataframe(pd.DataFrame(regioes), use_container_width=True)
        else:
            st.dataframe(datasetTempoTratamento.head(), use_container_width=True)
    except Exception as e:
        st.write("Dados de tempo por região disponíveis no dataset.")

st.divider()

# TABELA FINAL
# ==================================================================

st.subheader("📋 Top 10 - Maior Tempo de Acompanhamento")

if len(filtros_sobrev) > 0:
    top10 = (filtros_sobrev.nlargest(10, 'followupmonths')
             [['patientid', 'gender', 'age', 'tumortype', 'cancerstage',
               'survivalstatus', 'followupmonths']].reset_index(drop=True))
    st.dataframe(top10, use_container_width=True)

st.caption("Dashboard CANDI - Big Data em Saúde 🔬")
