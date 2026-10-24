from pathlib import Path

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

# Pontos de apoio fora do RJ, perto das divisas (coordenadas APROXIMADAS do centro da cidade)
# Coordenadas dos novos pontos = centro do município (aproximado)
# Trocado pelos dados reais do CNES (lat/long de cada hospital)
APOIO_FORA_RJ = [
    # --- Já existentes ---
    ("Juiz de Fora (MG)", -21.7642, -43.3503),
    ("Além Paraíba (MG)", -21.8878, -42.7092),
    ("Leopoldina (MG)", -21.5322, -42.6435),
    ("Cataguases (MG)", -21.3892, -42.6967),
    ("Muriaé (MG)", -21.1306, -42.3664),
    ("Caxambu (MG)", -21.9778, -44.9339),
    ("Cachoeiro de Itapemirim (ES)", -20.8489, -41.1129),
    ("Mimoso do Sul (ES)", -21.0636, -41.3622),
    ("Queluz (SP)", -22.5330, -44.7781),
    ("Cruzeiro (SP)", -22.5736, -44.9686),
    ("Lorena (SP)", -22.7306, -45.1244),
    ("Ubatuba (SP)", -23.4339, -45.0711),

    # --- Novos: SP ---
    ("Bananal (SP)", -22.6828, -44.3253),
    ("Areias (SP)", -22.5786, -44.7003),

    # --- Novos: MG ---
    ("Itamonte (MG)", -22.2850, -44.8683),
    ("Bocaina de Minas (MG)", -22.1481, -44.4186),
    ("Santa Rita de Jacutinga (MG)", -22.1469, -44.0956),  # Hosp. Monsenhor Marciano fica aqui
    ("Passa Vinte (MG)", -22.2078, -44.2478),  # local possível, hospital não confirmado
    ("Rio Preto (MG)", -22.0847, -43.8269),  # local possível, hospital esperado
    ("Simão Pereira (MG)", -21.9547, -43.3053),
    ("Mar de Espanha (MG)", -21.8708, -43.0108),
    ("Volta Grande (MG)", -21.7667, -42.5417),
    ("Pirapetinga (MG)", -21.6514, -42.3436),
    ("Palma (MG)", -21.3700, -42.3200),
    ("Patrocínio do Muriaé (MG)", -21.1547, -42.2128),
    ("Antônio Prado de Minas (MG)", -20.8900, -42.1000),
    ("Tombos (MG)", -20.9061, -42.0286),

    # --- Novos: ES ---
    ("São José do Calçado (ES)", -21.0231, -41.6511),
    ("Apiacá (ES)", -21.1522, -41.5681),
]


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

    df["nome_hospital"] = (
        df["no_fantasia"].fillna(df["no_razao_social"]).fillna("Unidade sem nome informado")
    )

    # Toda unidade com "UPA" no nome vira PRONTO ATENDIMENTO, mesmo que o CNES
    # tenha classificado em outro tipo (senão ela seria descartada pelo filtro abaixo)
    eh_upa = df["nome_hospital"].str.contains(r"\bUPA\b", case=False, regex=True)
    df.loc[eh_upa, "ds_tipo_unidade"] = "PRONTO ATENDIMENTO"

    df = df[df["ds_tipo_unidade"].isin(TIPOS_UNIDADES)].copy()

    df["latitude"] = pd.to_numeric(df["lat"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["long"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
    df["fora_rj"] = False  # unidades que vieram do CNES do RJ

    # Pontos de apoio fora do RJ, com as mesmas colunas usadas pelo resto do app
    apoio = pd.DataFrame(APOIO_FORA_RJ, columns=["cidade", "latitude", "longitude"])
    apoio["nome_hospital"] = "Rede de saúde de " + apoio["cidade"] + " (ponto aproximado)"
    apoio["ds_tipo_unidade"] = "HOSPITAL GERAL"
    apoio["fora_rj"] = True

    return pd.concat([df, apoio.drop(columns="cidade")], ignore_index=True)


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