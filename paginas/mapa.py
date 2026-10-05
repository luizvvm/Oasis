import pydeck as pdk
import streamlit as st

from utils import TIPOS_PADRAO, TIPOS_UNIDADES, load_hospitals

df = st.session_state["df_filtrado"]
hospitais = load_hospitals()

st.title("Mapa de acidentes e hospitais")

tipos = st.sidebar.multiselect(
    "Tipos de unidade de saúde:", TIPOS_UNIDADES, default=TIPOS_PADRAO
)
hospitais = hospitais[hospitais["ds_tipo_unidade"].isin(tipos)].copy()

c1, c2 = st.columns(2)
mostrar_acidentes = c1.toggle("Mostrar acidentes", value=True)
mostrar_hospitais = c2.toggle("Mostrar unidades de saúde", value=True)

# Textos do tooltip: cada camada tem o seu, então o hover não fica vazio
acidentes = df[["latitude", "longitude"]].copy()
acidentes["tooltip_html"] = (
    "<b>Acidente em " + df["municipio"].fillna("-") + "</b><br/>"
    + df["tipo_acidente"].fillna("-") + "<br/>"
    + df["nome_corredor"] + " km " + df["km"].astype(str) + "<br/>"
    + "Mortos: " + df["mortos"].astype(str)
    + " | Feridos: " + df["feridos"].astype(str)
)

icone = {
    "url": "data:image/svg+xml;charset=utf-8,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'%3E"
    "%3Crect x='8' y='8' width='48' height='48' fill='%231e64ff99' stroke='none'/%3E%3C/svg%3E",
    "width": 64,
    "height": 64,
    "anchorY": 32,
}
unidades = hospitais[["latitude", "longitude"]].copy()
unidades["icon_data"] = [icone] * len(unidades)
unidades["tooltip_html"] = (
    "<b>" + hospitais["nome_hospital"] + "</b><br/>"
    + hospitais["ds_tipo_unidade"] + "<br/>"
    + hospitais["municipio"].fillna("-") + " - " + hospitais["no_bairro"].fillna("-") + "<br/>"
    + hospitais["no_logradouro"].fillna("-") + ", " + hospitais["nu_endereco"].fillna("s/n").astype(str)
)

camadas = []
if mostrar_acidentes:
    camadas.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=acidentes,
            get_position=["longitude", "latitude"],
            get_color="[220, 50, 50, 180]",
            get_radius=250,
            radius_min_pixels=4,
            radius_max_pixels=15,
            pickable=True,
        )
    )
if mostrar_hospitais:
    camadas.append(
        pdk.Layer(
            "IconLayer",
            data=unidades,
            get_position=["longitude", "latitude"],
            get_icon="icon_data",
            get_size=500,
            size_units="meters",
            size_min_pixels=4,
            size_max_pixels=15,
            pickable=True,
        )
    )

mapa = pdk.Deck(
    layers=camadas,
    initial_view_state=pdk.ViewState(latitude=-22.5, longitude=-43.2, zoom=7, pitch=30),
    tooltip={"html": "{tooltip_html}", "style": {"backgroundColor": "white", "color": "black"}},
)

st.pydeck_chart(mapa, height=600)
st.caption(
    f"🔴 acidentes ({len(acidentes)}) | 🔵 unidades de saúde ({len(unidades)}). "
    "Os filtros de rodovia e gravidade afetam só os acidentes."
)
