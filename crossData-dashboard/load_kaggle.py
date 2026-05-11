from dotenv import load_dotenv
load_dotenv()

import os
import tempfile
import zipfile
import json
from pathlib import Path
import streamlit as st

DATASETS_DO_KAGGLE = {
    "dataSeria.csv":               ("erdemtaha/cancer-data",                                        "Cancer_Data.csv"),
    "datasetSUS.csv":              ("lhucastenorio/oncology-treatment-datasus-brazil-20132023",      "oncological_panel_datasus.csv"),
    "noticiasCancer.csv":          ("oliveiraexp/oncology-news-and-research-december-2025",          "CRx_DB_Q1_2026.csv"),
    "sentimentosOncologia.csv":    ("orvile/sentiments-in-oncology",                                "Sentiments in Oncology A Cancer treatment sentiment dataset/Sentiments_Oncology_dataset_After_Treatment.csv"),
    "sobrevivenciaCancer.csv":     ("sakshihulke/oncology-treatment-and-survival-analysis-dataset",  "cancer patient data.csv"),
    "tempoP_inicioTratamento.csv": ("rafaelasantosm/painel-oncologiabr",                            "PAINEL_ONCOLOGIABR17597133287.csv"),
}

_CACHE_DIR = Path(tempfile.gettempdir()) / "big_candi_datasets"


def _credenciais_kaggle():
    username = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")

    if username and key:
        kaggle_dir = Path.home() / ".kaggle"
        kaggle_dir.mkdir(exist_ok=True)
        kaggle_json = kaggle_dir / "kaggle.json"
        if not kaggle_json.exists():
            kaggle_json.write_text(json.dumps({"username": username, "key": key}))
            kaggle_json.chmod(0o600)

    import kaggle
    kaggle.api.authenticate()

def _baixar_datasets_kaggle(csv_destino: str, dest_dir: Path) -> Path:
    dest_path = dest_dir / csv_destino
    if dest_path.exists():
        return dest_path

    datasets_ref, nome_no_zip = DATASETS_DO_KAGGLE[csv_destino]

    import kaggle
    kaggle.api.dataset_download_files(
        datasets_ref,
        path=str(dest_dir),
        unzip=False,
        quiet=False,
    )

    zip_baixado = dest_dir / f"{datasets_ref.split('/')[-1]}.zip"
    with zipfile.ZipFile(zip_baixado, "r") as z:
        arquivos = z.namelist()

        if nome_no_zip:
            match = [f for f in arquivos if f.endswith(nome_no_zip)]
        else:
            match = [f for f in arquivos if f.lower().endswith(".csv")]
            if match:
                st.warning(
                    f"Nome real de `{csv_destino}` no zip: `{match[0]}` — "
                    f"adicione ao dicionário DATASETS_DO_KAGGLE para evitar este aviso."
                )

        if not match:
            raise FileNotFoundError(
                f"`{csv_destino}`: nenhum CSV encontrado no dataset '{datasets_ref}'. "
                f"Arquivos no zip: {arquivos}"
            )

        z.extract(match[0], path=dest_dir)
        extracted_path = dest_dir / match[0]
        if extracted_path != dest_path:
            extracted_path.rename(dest_path)

    zip_baixado.unlink(missing_ok=True)
    return dest_path

@st.cache_resource(show_spinner=False)
def get_datasets_path() -> dict[str, str]:
    _credenciais_kaggle()
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    paths = {}
    total = len(DATASETS_DO_KAGGLE)
    progresso = st.progress(0, text="📦 Baixando datasets do Kaggle...")

    for i, csv in enumerate(DATASETS_DO_KAGGLE):
        progresso.progress(i / total, text=f"⬇️ Baixando `{csv}`...")
        try:
            paths[csv] = str(_baixar_datasets_kaggle(csv, _CACHE_DIR))
        except Exception as e:
            st.error(f"Erro ao baixar `{csv}`: {e}")
            raise

    progresso.progress(1.0, text="✅ Datasets prontos!")
    progresso.empty()
    return paths