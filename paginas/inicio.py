import streamlit as st

from utils import load_data

df = load_data()

st.title("Projeto Oasis")
st.subheader("Acidentes nas rodovias federais do Rio de Janeiro e a rede de saúde ao redor")
st.write(
    "Este painel reúne os acidentes registrados pela Polícia Rodoviária Federal no estado "
    "do Rio de Janeiro e os mostra junto dos hospitais e pronto-atendimentos cadastrados no CNES. "
    "A ideia é entender onde, quando e por que os acidentes acontecem, e quão perto do socorro eles ocorrem."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ocorrências", f"{len(df):,}".replace(",", "."))
c2.metric("Vítimas fatais", int(df["mortos"].sum()))
c3.metric("Rodovias", df["nome_corredor"].nunique())
c4.metric(
    "Período",
    f"{df['data_inversa'].min():%d/%m} a {df['data_inversa'].max():%d/%m/%Y}",
)

st.markdown("---")
st.markdown("### O que você encontra aqui")

col_mapa, col_analises = st.columns(2)
with col_mapa:
    st.markdown("**Mapa**")
    st.write("Cada acidente e cada unidade de saúde no mapa, com detalhes ao passar o mouse.")
    st.page_link("paginas/mapa.py", label="Abrir o mapa", icon="🗺️")
with col_analises:
    st.markdown("**Análises**")
    st.write("Gráficos por horário, dia da semana, causa, severidade, clima e traçado da via.")
    st.page_link("paginas/analises.py", label="Abrir as análises", icon="📊")

st.markdown("---")
st.markdown("### De onde vêm os dados")
st.markdown(
    "- **Acidentes:** dados abertos da Polícia Rodoviária Federal (PRF), recorte do RJ em 2026.\n"
    "- **Unidades de saúde:** Cadastro Nacional de Estabelecimentos de Saúde (CNES/DATASUS).\n"
    "- Os filtros da barra lateral (rodovia e gravidade) valem para o Mapa e as Análises."
)

st.markdown("### Sobre o projeto")
st.write(
    "Projeto acadêmico de código aberto, feito com Python, Streamlit, Plotly e PyDeck. "
)
