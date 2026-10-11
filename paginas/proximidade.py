import numpy as np
import pydeck as pdk
import streamlit as st
from scipy.spatial import cKDTree

from utils import filtro_tipos_unidade, load_hospitals

st.title("🏥 Hospital mais próximo de cada acidente")

RAIO_TERRA_KM = 6371.0

df = st.session_state["df_filtrado"].dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
tipos = filtro_tipos_unidade()
hosp = load_hospitals()
hosp = hosp[hosp["ds_tipo_unidade"].isin(tipos)].reset_index(drop=True)

if hosp.empty:
    st.warning("Nenhum tipo de unidade selecionado. Escolha ao menos um na barra lateral.")
    st.stop()


@st.cache_data
def achar_mais_proximo(lat_a, lon_a, lat_h, lon_h):
    """Para cada acidente, devolve o índice do hospital mais próximo e a distância em km."""
    # lat/lon viram pontos 3D na esfera unitária (assim a distância euclidiana
    # entre dois pontos é monotônica com a distância real na superfície)
    def xyz(lat, lon):
        lat, lon = np.radians(lat), np.radians(lon)
        return np.column_stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])

    arvore = cKDTree(xyz(lat_h, lon_h))  # constrói o índice dos hospitais uma única vez
    corda, idx = arvore.query(xyz(lat_a, lon_a), k=1)  # busca vetorizada de todos os acidentes
    # corda (distância reta no espaço 3D) -> arco na superfície: d = 2R * arcsin(corda / 2)
    km = 2 * RAIO_TERRA_KM * np.arcsin(corda / 2)
    return idx, km


idx, km = achar_mais_proximo(
    df["latitude"].to_numpy(), df["longitude"].to_numpy(),
    hosp["latitude"].to_numpy(), hosp["longitude"].to_numpy(),
)
df["dist_km"] = km
df["hosp_i"] = idx  # posição do hospital dentro de hosp

c1, c2, c3 = st.columns(3)
c1.metric("Acidentes analisados", f"{len(df):,}".replace(",", "."))
c2.metric("Distância média ao hospital", f"{km.mean():.1f} km")
c3.metric("Pior caso", f"{km.max():.1f} km")

# Seleção anterior (o clique faz o app rodar de novo, então lemos do session_state)
sel = (
    st.session_state.get("mapa_prox", {})
    .get("selection", {})
    .get("objects", {})
    .get("acidentes", [])
)

# Dados enxutos pras camadas (só colunas simples, que serializam bem em JSON)
acid = df[["latitude", "longitude", "nome_corredor", "km", "dist_km"]].copy()
acid["i"] = df.index
acid["dist_txt"] = acid["dist_km"].round(1).astype(str)
hosp_map = hosp[["latitude", "longitude", "nome_hospital", "ds_tipo_unidade"]]

camadas = [
    pdk.Layer(
        "ScatterplotLayer", data=hosp_map, id="hospitais",
        get_position="[longitude, latitude]", get_radius=500,
        get_fill_color=[40, 200, 120, 200], pickable=True,
    ),
    pdk.Layer(
        "ScatterplotLayer", data=acid, id="acidentes",
        get_position="[longitude, latitude]", get_radius=350,
        get_fill_color=[230, 60, 60, 170], pickable=True, auto_highlight=True,
    ),
]

if sel:
    a = df.loc[sel[0]["i"]]
    h = hosp.loc[int(a["hosp_i"])]
    # linha ligando o acidente selecionado ao hospital mais próximo
    linha = [{
        "origem": [a["longitude"], a["latitude"]],
        "destino": [h["longitude"], h["latitude"]],
    }]
    camadas.append(pdk.Layer(
        "LineLayer", data=linha, get_source_position="origem",
        get_target_position="destino", get_color=[255, 255, 255], get_width=4,
    ))

mapa = pdk.Deck(
    layers=camadas,
    initial_view_state=pdk.ViewState(
        latitude=df["latitude"].mean(), longitude=df["longitude"].mean(), zoom=7.5,
    ),
    tooltip={"text": "{nome_corredor} km {km}\n{nome_hospital}\n{ds_tipo_unidade}"},
)

st.pydeck_chart(mapa, on_select="rerun", selection_mode="single-object", key="mapa_prox")

if sel:
    st.success(
        f"Acidente na {a['nome_corredor']} (km {a['km']}): hospital mais próximo é "
        f"**{h['nome_hospital']}** ({h['ds_tipo_unidade'].title()}), a **{a['dist_km']:.1f} km** em linha reta."
    )
else:
    st.caption("Clique em um ponto vermelho (acidente) para ver o hospital mais próximo. Pontos verdes são as unidades de saúde.")