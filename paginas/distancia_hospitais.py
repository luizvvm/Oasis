import pydeck as pdk
import streamlit as st

from utils import (
    acidentes_com_hospital_mais_proximo,
    filtro_tipos_unidade,
    load_hospitals,
)

df = st.session_state["df_filtrado"]
hospitais = load_hospitals()
tipos = filtro_tipos_unidade()
hospitais = hospitais[hospitais["ds_tipo_unidade"].isin(tipos)].copy()

st.title("Mapa: top 50 batidas mais longe dos hospitais")
st.caption(
    "Distância em linha reta entre as coordenadas da ocorrência e da unidade de saúde "
    "mais próxima; não representa distância por estrada nem tempo de viagem."
)

if hospitais.empty:
    st.warning("Selecione ao menos um tipo de unidade de saúde para comparar as distâncias.")
    st.stop()

acidentes_com_coordenadas = df.dropna(subset=["latitude", "longitude"])
if acidentes_com_coordenadas.empty:
    st.warning("Não há acidentes com coordenadas válidas nos filtros atuais.")
    st.stop()

ordenados = acidentes_com_hospital_mais_proximo(acidentes_com_coordenadas, hospitais)
top_50 = ordenados.sort_values(
    "distancia_hospital_km", ascending=False, kind="stable"
).head(50).copy()

st.subheader("Mapa das batidas mais distantes")

icone_hospital = {
    "url": "data:image/svg+xml;charset=utf-8,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'%3E"
    "%3Crect x='8' y='8' width='48' height='48' fill='%231e64ff99' stroke='none'/%3E%3C/svg%3E",
    "width": 64,
    "height": 64,
    "anchorY": 32,
}

top_50["distancia_label"] = top_50["distancia_hospital_km"].map(lambda km: f"{km:.2f} km")
top_50["data_label"] = top_50["data_inversa"].dt.strftime("%d/%m/%Y").fillna("-")
top_50["tooltip_html"] = (
    "<b>Batida — " + top_50["municipio"].fillna("-") + "</b><br/>"
    + top_50["nome_corredor"].fillna("-")
    + " km "
    + top_50["km"].fillna("-").astype(str)
    + "<br/>"
    + top_50["data_label"]
    + " às "
    + top_50["horario"].fillna("-")
    + "<br/>Até "
    + top_50["hospital_mais_proximo"].fillna("-")
    + "<br/><b>Distância: "
    + top_50["distancia_label"]
    + "</b>"
)

unidades = top_50.drop_duplicates(
    subset=["hospital_latitude", "hospital_longitude"]
).copy()
unidades["icon_data"] = [icone_hospital] * len(unidades)
unidades["tooltip_html"] = (
    "<b>"
    + unidades["hospital_mais_proximo"].fillna("-")
    + "</b><br/>"
    + unidades["tipo_unidade_mais_proxima"].fillna("-")
    + "<br/>"
    + unidades["municipio_hospital"].fillna("-")
)

linhas = top_50.rename(
    columns={
        "longitude": "acidente_longitude",
        "latitude": "acidente_latitude",
    }
)
camadas = [
    pdk.Layer(
        "LineLayer",
        data=linhas,
        get_source_position=["acidente_longitude", "acidente_latitude"],
        get_target_position=["hospital_longitude", "hospital_latitude"],
        get_color=[80, 80, 80, 130],
        get_width=1,
        width_min_pixels=1,
    ),
    pdk.Layer(
        "ScatterplotLayer",
        data=top_50,
        get_position=["longitude", "latitude"],
        get_fill_color="[220, 50, 50, 200]",
        get_radius=350,
        radius_min_pixels=5,
        radius_max_pixels=15,
        pickable=True,
    ),
    pdk.Layer(
        "IconLayer",
        data=unidades,
        get_position=["hospital_longitude", "hospital_latitude"],
        get_icon="icon_data",
        get_size=500,
        size_units="meters",
        size_min_pixels=5,
        size_max_pixels=16,
        pickable=True,
    ),
]

mapa = pdk.Deck(
    layers=camadas,
    initial_view_state=pdk.ViewState(
        latitude=top_50["latitude"].mean(),
        longitude=top_50["longitude"].mean(),
        zoom=6,
        pitch=0,
    ),
    tooltip={"html": "{tooltip_html}", "style": {"backgroundColor": "white", "color": "black"}},
)
st.pydeck_chart(mapa, height=550)
st.caption(
    f"🔴 batidas ({len(top_50)}) | 🔵 hospitais/unidades mais próximos "
    f"({len(unidades)}). As linhas ligam cada ocorrência à unidade atribuída."
)

st.subheader("Ordem das batidas mais longe dos hospitais")
ranking = top_50[
    [
        "data_inversa",
        "horario",
        "nome_corredor",
        "km",
        "municipio",
        "distancia_hospital_km",
        "hospital_mais_proximo",
        "tipo_unidade_mais_proxima",
        "municipio_hospital",
    ]
].rename(
    columns={
        "data_inversa": "Data",
        "horario": "Horário",
        "nome_corredor": "Rodovia",
        "km": "Km",
        "municipio": "Município da batida",
        "distancia_hospital_km": "Distância (km)",
        "hospital_mais_proximo": "Unidade mais próxima",
        "tipo_unidade_mais_proxima": "Tipo da unidade",
        "municipio_hospital": "Município da unidade",
    }
)
ranking.insert(0, "Ordem", range(1, len(ranking) + 1))
st.dataframe(
    ranking,
    width="stretch",
    hide_index=True,
    column_config={
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        "Distância (km)": st.column_config.NumberColumn("Distância (km)", format="%.2f"),
    },
)
