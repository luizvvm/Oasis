import streamlit as st

from utils import load_data

df = load_data()

# Espaçamento da apresentação do projeto
st.markdown(
    """<style>
    [data-testid="stMainBlockContainer"] { padding-top: 2.5rem; padding-bottom: 0; gap: clamp(0.5rem, 1.3vh, 1rem); }
    [data-testid="stMainBlockContainer"] hr { margin: clamp(0.5rem, 1.3vh, 1rem) 0; }
    [data-testid="stMainBlockContainer"] h1 { padding: 0 0 clamp(0.25rem, 1vh, 0.75rem) 0; }
    [data-testid="stMainBlockContainer"] h3 { padding: clamp(0.25rem, 1vh, 0.75rem) 0; }
    </style>""",
    unsafe_allow_html=True,
)

st.title("Projeto Oasis")
st.subheader("Acidentes nas rodovias federais do Rio de Janeiro e a rede de saúde ao redor")
st.write(
    "Este painel reúne os acidentes registrados pela Polícia Rodoviária Federal no estado "
    "do Rio de Janeiro e os mostra junto dos hospitais e pronto-atendimentos cadastrados no CNES. "
    "Use as abas para explorar a localização das ocorrências, investigar seus padrões "
    "e consultar as distâncias às unidades de saúde."
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
st.markdown("### Como explorar o projeto")
st.caption("Escolha a aba de acordo com a pergunta que você quer investigar.")

col_mapa, col_analises, col_distancia = st.columns(3)
with col_mapa:
    st.markdown("**Mapa**")
    st.write("**Onde estão os acidentes?** Explore os pontos, o mapa de calor e as áreas de risco junto das unidades de saúde.")
    st.page_link("paginas/mapa.py", label="Abrir o mapa", icon="🗺️")
with col_analises:
    st.markdown("**Análises**")
    st.write("**Quando e em quais condições ocorrem?** Compare horários, dias, causas, gravidade, clima e características das vias.")
    st.page_link("paginas/analises.py", label="Abrir as análises", icon="📊")
with col_distancia:
    st.markdown("**Distância dos hospitais**")
    st.write("**Quais ocorrências ficam mais longe das unidades?** Consulte o mapa e o ranking dos 50 acidentes mais distantes da unidade considerada mais próxima.")
    st.page_link(
        "paginas/distancia_hospitais.py",
        label="Consultar distâncias",
        icon="🏥",
    )

st.markdown("---")
st.markdown("### De onde vêm os dados")
st.markdown(
    "- **Acidentes:** dados abertos da Polícia Rodoviária Federal (PRF), recorte do RJ em 2026.\n"
    "- **Unidades de saúde:** Cadastro Nacional de Estabelecimentos de Saúde (CNES/DATASUS).\n"
    "- **Período da base:** "
    + f"{df['data_inversa'].min():%d/%m/%Y} a {df['data_inversa'].max():%d/%m/%Y}.\n"
    + "- **Filtros:** os grupos de rodovias selecionados acompanham a navegação entre Mapa, Análises e Distância dos hospitais."
)

st.markdown("### Sobre o projeto")
st.write(
    "Projeto acadêmico de código aberto, feito com Python, Streamlit, Plotly e PyDeck. "
)
