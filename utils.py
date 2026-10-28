from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

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


@st.cache_data
def acidentes_com_hospital_mais_proximo(acidentes, hospitais):
    """Associa cada acidente à unidade mais próxima pela distância geodésica em linha reta."""
    acidentes = acidentes.dropna(subset=["latitude", "longitude"]).copy().reset_index(drop=True)
    hospitais = hospitais.dropna(subset=["latitude", "longitude"]).copy().reset_index(drop=True)

    lat_acidentes = np.radians(acidentes["latitude"].to_numpy(dtype=float))
    lon_acidentes = np.radians(acidentes["longitude"].to_numpy(dtype=float))
    lat_hospitais = np.radians(hospitais["latitude"].to_numpy(dtype=float))
    lon_hospitais = np.radians(hospitais["longitude"].to_numpy(dtype=float))
    indices_hospital = np.empty(len(acidentes), dtype=int)
    distancias_km = np.empty(len(acidentes), dtype=float)

    for inicio in range(0, len(acidentes), 256):
        fim = min(inicio + 256, len(acidentes))
        delta_lat = lat_hospitais[None, :] - lat_acidentes[inicio:fim, None]
        delta_lon = lon_hospitais[None, :] - lon_acidentes[inicio:fim, None]
        haversine = (
            np.sin(delta_lat / 2) ** 2
            + np.cos(lat_acidentes[inicio:fim, None])
            * np.cos(lat_hospitais[None, :])
            * np.sin(delta_lon / 2) ** 2
        )
        distancias = 2 * 6371 * np.arcsin(np.sqrt(np.clip(haversine, 0, 1)))
        indices_hospital[inicio:fim] = distancias.argmin(axis=1)
        distancias_km[inicio:fim] = distancias.min(axis=1)

    unidade_mais_proxima = hospitais.iloc[indices_hospital].reset_index(drop=True)
    acidentes["distancia_hospital_km"] = distancias_km
    acidentes["hospital_mais_proximo"] = unidade_mais_proxima["nome_hospital"]
    acidentes["tipo_unidade_mais_proxima"] = unidade_mais_proxima["ds_tipo_unidade"]
    acidentes["municipio_hospital"] = unidade_mais_proxima["municipio"].fillna("-")
    acidentes["hospital_latitude"] = unidade_mais_proxima["latitude"].to_numpy()
    acidentes["hospital_longitude"] = unidade_mais_proxima["longitude"].to_numpy()
    return acidentes


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
