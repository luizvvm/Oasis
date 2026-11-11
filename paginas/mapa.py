import pydeck as pdk
import streamlit as st

from riscos import areas_de_risco
from utils import filtro_areas_risco, filtro_tipos_unidade, load_hospitals

df = st.session_state["df_filtrado"]
hospitais = load_hospitals()

# Espaçamento do mapa e das explicações das camadas
st.markdown(
    """<style>
    [data-testid="stMainBlockContainer"] { padding-top: 3rem; padding-bottom: 0; }
    </style>""",
    unsafe_allow_html=True,
)

st.title("Mapa")
st.caption(
    "Onde estão os acidentes? Explore as ocorrências em pontos ou no mapa de calor "
    "e veja os agrupamentos distantes das unidades de saúde com a camada de áreas de risco."
)

tipos = filtro_tipos_unidade()
hospitais = hospitais[hospitais["ds_tipo_unidade"].isin(tipos)].copy()

visualizacao = st.sidebar.radio(
    "Visualização dos acidentes",
    ["Mapa de calor", "Pontos"],
    help="O mapa de calor destaca a concentração de ocorrências; cada acidente tem o mesmo peso.",
)
raio_calor = 40
if visualizacao == "Mapa de calor":
    raio_calor = st.sidebar.slider(
        "Raio do mapa de calor (pixels)",
        min_value=10,
        max_value=100,
        value=40,
        step=5,
        help="Valores maiores espalham o calor e agrupam ocorrências próximas visualmente.",
    )

top_n, limite_km, min_batidas = filtro_areas_risco()

c0, c1, c2, c3 = st.columns([2, 1, 1, 1], vertical_alignment="center")
c0.markdown("**Camadas do mapa**")
mostrar_acidentes = c1.toggle("Mostrar acidentes", value=True)
mostrar_hospitais = c2.toggle("Mostrar unidades de saúde", value=True)

mostrar_areas = c3.toggle(
    "Mostrar áreas de risco",
    value=True,
    help="Retângulos em volta das batidas mais distantes de unidades de saúde. "
    "Batidas próximas entre si formam uma única área.",
)


@st.cache_data
def calcular_areas(acidentes, unidades, top_n, limite_km, min_batidas):
    return areas_de_risco(
        acidentes, unidades, top_n=top_n, limite_km=limite_km, min_batidas=min_batidas
    )


# As áreas dependem das unidades de saúde selecionadas: sem nenhuma, não há distância a medir
batidas_top, areas = calcular_areas(df, hospitais, top_n, limite_km, min_batidas)
if mostrar_areas and hospitais.empty:
    st.warning("Selecione ao menos um tipo de unidade de saúde para calcular as áreas de risco.")
elif mostrar_areas and areas.empty:
    st.info(
        "Nenhuma área encontrada com os critérios atuais. "
        "Em Parâmetros das áreas de risco, aumente a quantidade de acidentes considerados "
        "ou a distância de agrupamento, ou reduza o mínimo de acidentes por área."
    )

# Textos do tooltip: cada camada tem o seu, então o hover não fica vazio
acidentes = df[["latitude", "longitude"]].dropna().copy()
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
if mostrar_areas and not areas.empty:
    areas = areas.assign(
        tooltip_html=(
            "<b>Área de risco #" + (areas.index + 1).astype(str) + "</b><br/>"
            + areas["n_batidas"].astype(str) + " batidas entre as mais distantes<br/>"
            + "Distância da unidade mais próxima: média "
            + areas["dist_media_km"].round(1).astype(str) + " km, máx "
            + areas["dist_max_km"].round(1).astype(str) + " km<br/>"
            + areas["rodovias"] + " · " + areas["municipios"] + "<br/>"
            + "Mortos: " + areas["mortos"].astype(str) + " | Feridos: " + areas["feridos"].astype(str)
        )
    )
    camadas.append(
        pdk.Layer(
            "PolygonLayer",
            data=areas,
            get_polygon="polygon",
            get_fill_color=[255, 140, 0, 60],
            get_line_color=[255, 140, 0, 255],
            line_width_min_pixels=2,
            stroked=True,
            filled=True,
            pickable=True,
        )
    )
if mostrar_acidentes:
    if visualizacao == "Mapa de calor":
        camadas.append(
            pdk.Layer(
                "HeatmapLayer",
                data=acidentes[["latitude", "longitude"]],
                get_position=["longitude", "latitude"],
                get_weight=1,
                aggregation="SUM",
                radius_pixels=raio_calor,
                intensity=1,
                threshold=0.05,
                color_range=[
                    [255, 255, 178],
                    [254, 217, 118],
                    [254, 178, 76],
                    [253, 141, 60],
                    [240, 59, 32],
                    [189, 0, 38],
                ],
                pickable=False,
            )
        )
    else:
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
if mostrar_areas and not batidas_top.empty:
    destaque = batidas_top[["latitude", "longitude"]].copy()
    destaque["tooltip_html"] = (
        "<b>Batida entre as mais distantes</b><br/>"
        + batidas_top["dist_unidade_km"].round(1).astype(str) + " km da unidade mais próxima<br/>"
        + batidas_top["nome_corredor"] + " km " + batidas_top["km"].astype(str)
        + " · " + batidas_top["municipio"].fillna("-")
    )
    camadas.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=destaque,
            get_position=["longitude", "latitude"],
            get_color="[255, 140, 0, 255]",
            get_line_color="[0, 0, 0, 255]",
            stroked=True,
            line_width_min_pixels=1,
            get_radius=300,
            radius_min_pixels=5,
            radius_max_pixels=16,
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

st.pydeck_chart(mapa, height=480)
legendas = []
if mostrar_acidentes:
    if visualizacao == "Mapa de calor":
        legendas.append(
            f"🟡 → 🔴 calor: menor → maior concentração de acidentes ({len(acidentes)} ocorrências)"
        )
    else:
        legendas.append(f"🔴 pontos vermelhos: acidentes ({len(acidentes)})")
if mostrar_hospitais:
    legendas.append(f"🟦 quadrados azuis: unidades de saúde ({len(unidades)})")
if mostrar_areas and not areas.empty:
    legendas.append(
        "🟧 retângulos laranja: agrupamentos de acidentes distantes das unidades de saúde"
    )
if mostrar_areas and not batidas_top.empty:
    legendas.append(
        f"🟠 pontos laranja: acidentes mais distantes considerados ({len(batidas_top)})"
    )
st.caption(" | ".join(legendas) if legendas else "Nenhuma camada visível. Ative uma das opções acima.")
if mostrar_acidentes and visualizacao == "Mapa de calor":
    st.caption(
        "Concentração relativa no recorte atual; as cores se ajustam aos filtros e ao zoom. "
        "Use a opção Pontos para consultar os detalhes de cada acidente."
    )

if mostrar_areas and not areas.empty:
    st.caption(
        f"🟧 {len(areas)} áreas de risco a partir das {len(batidas_top)} batidas mais distantes de "
        f"unidades de saúde (de {batidas_top['dist_unidade_km'].min():.1f} a "
        f"{batidas_top['dist_unidade_km'].max():.1f} km). Batidas a até {limite_km:g} km umas das "
        f"outras formam uma área; áreas com menos de {min_batidas} batidas não são desenhadas."
    )
