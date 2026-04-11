<div align="center">

# Dashboard-BDN007-2026

Repositório de exercícios e projetos da disciplina de **Business Intelligence & Big Data** — Grupo 1 "Candi" · Fatec São Caetano do Sul · 2026

</div>

---

## 👥 Grupo 1 — Candi

Projeto desenvolvido para a disciplina **BDN007 — Business Intelligence e Big Data**  
Fatec São Caetano do Sul · 2026

- Carolina Pichelli Souza
- Fernando Alcantara D'Avila
- Guilherme Xavier Zanetti
- Heloísa Pichelli Souza
- Lucas Batista Sousa
- Nuno Kazuo Tronco Yokoji

---

## 📁 Estrutura do Repositório

```
Dashboard-BDN007-2026/
├── cancerPatientData-dashboard/   # Dashboard clínico individual (dataset único)
│
└── crossData-dashboard/           # Dashboard de análise cruzada (múltiplos datasets)
    ├── dados-candi-API/           # Código fonte da API de importação dos dados do CANDI
    ├── main.py                    # Aplicação Streamlit principal
    ├── main.ipynb                 # Notebook de exploração dos datasets
    ├── load_datasets.py           # Módulo de carregamento lazy/eager dos datasets
    └── requirements.txt           # Dependências do projeto
```

---

## 📊 Dashboard N1

### `crossData-dashboard` — Dashboard de Análise Cruzada

Dashboard de análise integrada que cruza **8 fontes de dados** distintas sobre oncologia, incluindo dados reais do projeto Candi, datasets do Kaggle e dados abertos do SUS.

#### 📂 `dados-candi-API`

Diretório contendo os dados exportados diretamente da API do projeto Candi — incluindo os registros de sentimentos (`candiSentimentos.csv`) e sintomas (`candiSintomas.csv`) dos pacientes, utilizados nas análises cruzadas do dashboard.

**Datasets utilizados:**

| Arquivo | Origem | Descrição |
|---|---|---|
| `dataSeria.csv` | Kaggle | Dataset Wisconsin — características físicas de tumores |
| `datasetSUS.csv` | Kaggle | Dados de pacientes oncológicos no SUS (dataset grande, tratado com Dask) |
| `noticiasCancer.csv` | Kaggle | Artigos científicos e jornalísticos sobre câncer |
| `sentimentosOncologia.csv` | Kaggle | Comentários de pacientes oncológicos (EN) com análise de sentimento |
| `sobrevivenciaCancer.csv` | Kaggle | Taxas de sobrevivência por tipo de tumor e estágio |
| `tempoP_inicioTratamento.csv` | Kaggle | Tempo até início do tratamento por região brasileira |

**Principais funcionalidades:**
- Análise epidemiológica do SUS (distribuição por sexo, ano, UF)
- Taxa de sobrevivência por tipo de tumor e estágio
- Correlação entre características tumorais (heatmap)
- Sentimentos e sintomas do Candi (linha do tempo + top sintomas)
- **Análise cruzada:** distribuição etária CANDI vs Sobrevivência, severidade Wisconsin vs Sobrevivência, felicidade CANDI vs estágios
- Tempo para início do tratamento por região

**Stack:** Python · Streamlit · Plotly · Pandas · Dask · NumPy

**Para rodar:**
```bash
cd crossData-dashboard
pip install -r requirements.txt
# Coloque todos os arquivos .csv dentro da pasta /crossData-dashboard
streamlit run main.py
```

> ⚠️ **Atenção:** O `datasetSUS.csv` é grande. O dashboard usa processamento lazy com Dask e oferece modo de amostragem para melhor performance.

---

## ⚙️ Requisitos Gerais

- Python 3.10+
- Os arquivos `.csv` externos **não estão versionados** (`.gitignore`). Cada membro do grupo deve obtê-los separadamente via Google Drive:
https://drive.google.com/drive/folders/1MSed8fKre69DQWLBioCEkIilW_97t7HT?usp=sharing
