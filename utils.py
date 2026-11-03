from pathlib import Path

import pandas as pd
import streamlit as st

from riscos import LIMITE_KM_PADRAO, MIN_BATIDAS_PADRAO, TOP_N_PADRAO

PASTA = Path(__file__).parent

# Tipos de unidade do CNES que podem aparecer no mapa
TIPOS_UNIDADES = [
    "HOSPITAL GERAL",
    "HOSPITAL ESPECIALIZADO",
    "PRONTO SOCORRO GERAL",
    "PRONTO SOCORRO ESPECIALIZADO",
    "PRONTO ATENDIMENTO",
    "HOSPITAL/DIA - ISOLADO",
]
# Hospital-dia não atende emergência, por isso começa desmarcado
TIPOS_PADRAO = TIPOS_UNIDADES[:-1]


@st.cache_data
def load_data():
    df = pd.read_csv(PASTA / "datatran2026_rj.csv")
    df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")
    if "hora" not in df.columns:
        df["hora"] = pd.to_datetime(
            df["horario"], format="%H:%M:%S", errors="coerce"
        ).dt.hour
    return df


@st.cache_data
def load_hospitals():
    df = pd.read_csv(
        PASTA / "cnes_ativo_esp_RJ.csv", sep=None, engine="python", encoding="latin1"
    )
    df = df[df["ds_tipo_unidade"].isin(TIPOS_UNIDADES)].copy()

    df["latitude"] = pd.to_numeric(df["lat"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["long"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])

    df["nome_hospital"] = (
        df["no_fantasia"].fillna(df["no_razao_social"]).fillna("Unidade sem nome informado")
    )
    return df


# Grupos de rodovias (por volume de ocorrências), pra não listar cada BR solta
GRUPOS_RODOVIAS = {
    "Principais": ["BR-101", "BR-116", "BR-040"],
    "Regionais": ["BR-393", "BR-493", "BR-465", "BR-356"],
    "Trechos curtos": ["BR-495", "BR-354", "BR-485"],
}

# Nome amigável e explicação de cada tipo de unidade do CNES
DESCRICAO_UNIDADES = {
    "HOSPITAL GERAL": ("Hospital geral", "Atende várias especialidades e tem internação."),
    "HOSPITAL ESPECIALIZADO": (
        "Hospital especializado",
        "Focado em uma área (ex.: ortopedia, cardiologia, trauma).",
    ),
    "PRONTO SOCORRO GERAL": ("Pronto-socorro geral", "Urgência e emergência de qualquer tipo."),
    "PRONTO SOCORRO ESPECIALIZADO": (
        "Pronto-socorro especializado",
        "Urgência e emergência de uma área específica.",
    ),
    "PRONTO ATENDIMENTO": (
        "Pronto atendimento (UPA)",
        "Casos de urgência de média complexidade, sem internação longa.",
    ),
    "HOSPITAL/DIA - ISOLADO": (
        "Hospital-dia",
        "Cirurgias e procedimentos sem pernoite. Não atende emergência.",
    ),
}
GRUPOS_UNIDADES = {
    "Hospitais": ["HOSPITAL GERAL", "HOSPITAL ESPECIALIZADO"],
    "Urgência e emergência": [
        "PRONTO SOCORRO GERAL",
        "PRONTO SOCORRO ESPECIALIZADO",
        "PRONTO ATENDIMENTO",
    ],
    "Outros": ["HOSPITAL/DIA - ISOLADO"],
}


def filtros_sidebar(df):
    """Filtros compartilhados pelas páginas Mapa e Análises."""
    st.sidebar.header("Filtros de pesquisa")

    existentes = set(df["nome_corredor"].dropna().unique())
    grupos = {
        nome: [br for br in brs if br in existentes] for nome, brs in GRUPOS_RODOVIAS.items()
    }
    # BRs que não estão em nenhum grupo não podem sumir do filtro
    agrupadas = {br for brs in grupos.values() for br in brs}
    sobras = sorted(existentes - agrupadas)
    if sobras:
        grupos["Outras"] = sobras
    grupos = {nome: brs for nome, brs in grupos.items() if brs}

    st.sidebar.markdown("Rodovias (BRs):")
    sel_grupos = [
        g for g, brs in grupos.items()
        if st.sidebar.checkbox(
            f"{g} · {', '.join(b.replace('BR-', '') for b in brs)}",
            value=True,
            key=f"grupo_{g}",
            help="Grupos organizados pelo volume de ocorrências. Os números são as BRs de cada grupo.",
        )
    ]
    sel_br = [br for g in sel_grupos for br in grupos[g]]

    return df[df["nome_corredor"].isin(sel_br)].copy()


def filtro_tipos_unidade():
    """Dropdown detalhado de tipos de unidade de saúde; devolve os tipos marcados."""
    st.sidebar.markdown("Tipos de unidade de saúde:")
    selecionados = []
    with st.sidebar.popover("Escolher tipos de unidade", width="stretch"):
        for grupo, tipos in GRUPOS_UNIDADES.items():
            st.markdown(f"**{grupo}**")
            for tipo in tipos:
                nome, descricao = DESCRICAO_UNIDADES[tipo]
                if st.checkbox(nome, value=tipo in TIPOS_PADRAO, help=descricao, key=f"tipo_{tipo}"):
                    selecionados.append(tipo)
    st.sidebar.caption(f"{len(selecionados)} de {len(TIPOS_UNIDADES)} tipos selecionados")
    return selecionados


def filtro_areas_risco():
    """Parâmetros das áreas de risco (batidas longe de unidades de saúde); devolve (top_n, limite_km, min_batidas)."""
    st.sidebar.markdown("Áreas de risco:")
    top_n = st.sidebar.number_input(
        "Quantidade de batidas mais distantes",
        min_value=5, max_value=500, value=TOP_N_PADRAO, step=5,
        help="Quantas batidas, das mais longe de uma unidade de saúde para as mais perto, entram no cálculo.",
    )
    limite_km = st.sidebar.slider(
        "Distância máxima entre batidas da mesma área (km)",
        min_value=0.5, max_value=10.0, value=LIMITE_KM_PADRAO, step=0.5,
        help="Batidas a até essa distância uma da outra (mesmo que por 'vizinhas de vizinhas') "
        "viram uma única área. Acima de ~3 km áreas distintas começam a se fundir em retângulos enormes.",
    )
    min_batidas = st.sidebar.number_input(
        "Mínimo de batidas por área",
        min_value=1, max_value=10, value=MIN_BATIDAS_PADRAO, step=1,
        help="Áreas com menos batidas que isso não são desenhadas (uma batida isolada não é uma área).",
    )
    return int(top_n), float(limite_km), int(min_batidas)
