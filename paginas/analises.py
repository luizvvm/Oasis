import plotly.express as px
import streamlit as st

df = st.session_state["df_filtrado"]

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def contagem(serie, nome, top=None):
    c = serie.value_counts()
    if top:
        c = c.head(top)
    return c.rename_axis(nome).reset_index(name="quantidade")


def barras(dados, categoria, cor, horizontal=False, rotulo=None):
    rotulos = {categoria: rotulo or categoria, "quantidade": "Ocorrências"}
    if horizontal:
        fig = px.bar(dados, x="quantidade", y=categoria, orientation="h",
                     labels=rotulos, color_discrete_sequence=[cor])
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
    else:
        fig = px.bar(dados, x=categoria, y="quantidade",
                     labels=rotulos, color_discrete_sequence=[cor])
    st.plotly_chart(fig, width="stretch")


st.title("Análises dos acidentes")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de ocorrências", len(df))
c2.metric("Vítimas fatais", int(df["mortos"].sum()))
c3.metric("Feridos graves", int(df["feridos_graves"].sum()))
c4.metric("Feridos leves", int(df["feridos_leves"].sum()))

tab_temporal, tab_causas, tab_via = st.tabs(
    ["Análise temporal", "Causas e severidade", "Infraestrutura e clima"]
)

with tab_temporal:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Ocorrências por horário do dia**")
        por_hora = df.groupby("hora").size().reindex(range(24), fill_value=0)
        barras(por_hora.rename_axis("hora").reset_index(name="quantidade"), "hora", "#1f77b4", rotulo="Hora")
    with col2:
        st.markdown("**Ocorrências por dia da semana**")
        por_dia = df["dia_semana"].value_counts().reindex(DIAS, fill_value=0)
        barras(por_dia.rename_axis("dia_semana").reset_index(name="quantidade"), "dia_semana", "#2ca02c", rotulo="Dia")
    st.markdown("**Ocorrências por fase do dia**")
    barras(contagem(df["fase_dia"], "fase_dia"), "fase_dia", "#9467bd", rotulo="Fase do dia")

with tab_causas:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Principais tipos de acidente**")
        barras(contagem(df["tipo_acidente"], "tipo_acidente", 8), "tipo_acidente", "#ff7f0e",
               horizontal=True, rotulo="Tipo")
    with col2:
        st.markdown("**Classificação por severidade**")
        fig = px.pie(contagem(df["classificacao_acidente"], "classificacao"),
                     names="classificacao", values="quantidade", hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, width="stretch")
    st.markdown("**Top 10 principais causas**")
    top_causas = contagem(df["causa_acidente"], "Causa do acidente", 10)
    st.dataframe(top_causas.rename(columns={"quantidade": "Total de ocorrências"}),
                 width="stretch", hide_index=True)

with tab_via:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Condições meteorológicas**")
        barras(contagem(df["condicao_metereologica"], "condicao"), "condicao", "#17becf", rotulo="Clima")
    with col2:
        st.markdown("**Traçado da via**")
        barras(contagem(df["tracado_via"], "tracado", 6), "tracado", "#8c564b",
               horizontal=True, rotulo="Traçado")
    st.markdown("**Municípios com maior volume de ocorrências**")
    top_mun = contagem(df["municipio"], "Município", 10)
    st.dataframe(top_mun.rename(columns={"quantidade": "Total de acidentes"}),
                 width="stretch", hide_index=True)

with st.expander("Exibir base de dados em tabela"):
    st.dataframe(
        df[["data_inversa", "horario", "nome_corredor", "km", "municipio", "tipo_acidente",
            "classificacao_acidente", "causa_acidente", "mortos", "feridos"]],
        width="stretch",
        hide_index=True,
    )
