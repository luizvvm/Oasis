import streamlit as st

from utils import filtros_sidebar, load_data

st.set_page_config(page_title="Projeto Oasis - Acidentes RJ", page_icon="🚑", layout="wide")

pg = st.navigation(
    [
        st.Page("paginas/inicio.py", title="Início", icon="🏠", default=True),
        st.Page("paginas/mapa.py", title="Mapa", icon="🗺️"),
        st.Page("paginas/analises.py", title="Análises", icon="📊"),
    ]
)

# Os filtros ficam aqui para valer em todas as páginas que usam dados filtrados
if pg.title != "Início":
    df_filtrado = filtros_sidebar(load_data())
    if df_filtrado.empty:
        st.warning("Nenhuma ocorrência com os filtros atuais. Ajuste os filtros na barra lateral.")
        st.stop()
    st.session_state["df_filtrado"] = df_filtrado

pg.run()
