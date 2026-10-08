import plotly.express as px
import streamlit as st

df = st.session_state["df_filtrado"]

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def contagem(serie, nome, top=None):
    c = serie.value_counts()
    if top:
        c = c.head(top)
    return c.rename_axis(nome).reset_index(name="quantidade")


def barras(dados, categoria, cor, rotulo=None, hover=None):
    """Barras verticais. `hover` é uma coluna com o texto do tooltip no lugar do valor do eixo."""
    nome = rotulo or categoria
    fig = px.bar(dados, x=categoria, y="quantidade", color_discrete_sequence=[cor],
                 labels={categoria: nome, "quantidade": "Ocorrências"})
    fig.update_traces(
        customdata=dados[[hover or categoria]],
        hovertemplate=f"{nome}: %{{customdata[0]}}<br>Ocorrências: %{{y}}<extra></extra>",
    )
    st.plotly_chart(fig, width="stretch")


periodo = f"{df['data_inversa'].min():%d/%m/%Y} a {df['data_inversa'].max():%d/%m/%Y}"

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
        st.markdown("**Total de ocorrências por horário do dia**")
        st.caption(f"Soma de todos os dias do período ({periodo}), não a média por dia.")
        por_hora = df.groupby("hora").size().reindex(range(24), fill_value=0)
        por_hora = por_hora.rename_axis("hora").reset_index(name="quantidade")
        por_hora["faixa"] = por_hora["hora"].map(lambda h: f"{h}:00-{h + 1}:00")
        barras(por_hora, "hora", "#1f77b4", rotulo="Hora", hover="faixa")
    with col2:
        st.markdown("**Total de ocorrências por dia da semana**")
        st.caption(f"Soma de todas as semanas do período ({periodo}).")
        por_dia = df["dia_semana"].value_counts().reindex(DIAS, fill_value=0)
        barras(por_dia.rename_axis("dia_semana").reset_index(name="quantidade"), "dia_semana", "#2ca02c", rotulo="Dia")
    st.markdown("**Ocorrências por fase do dia**")
    barras(contagem(df["fase_dia"], "fase_dia"), "fase_dia", "#9467bd", rotulo="Fase do dia")
    st.markdown(
        "- **Amanhecer:** período do nascer do sol, em que a luz ainda é fraca.\n"
        "- **Pleno dia:** dia claro, com boa visibilidade.\n"
        "- **Anoitecer:** período do pôr do sol, em que a luz vai acabando.\n"
        "- **Plena noite:** noite fechada, sem luz natural."
    )

with tab_causas:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Principais tipos de acidente**")
        barras(contagem(df["tipo_acidente"], "tipo_acidente", 8), "tipo_acidente", "#ff7f0e",
               rotulo="Tipo")
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
        tracado = contagem(df["tracado_via"].str.replace(";", ", "), "tracado", 6)
        barras(tracado, "tracado", "#8c564b", rotulo="Traçado")
    st.markdown("**Municípios com maior volume de ocorrências**")
    top_mun = contagem(df["municipio"], "Município", 10)
    st.dataframe(top_mun.rename(columns={"quantidade": "Total de acidentes"}),
                 width="stretch", hide_index=True)

COLUNAS_TABELA = {
    "data_inversa": "Data",
    "horario": "Horário",
    "nome_corredor": "Rodovia",
    "km": "Km",
    "municipio": "Município",
    "tipo_acidente": "Tipo de acidente",
    "classificacao_acidente": "Classificação",
    "causa_acidente": "Causa",
    "mortos": "Mortos",
    "feridos": "Feridos",
}

with st.expander("Exibir base de dados em tabela"):
    st.dataframe(
        df[list(COLUNAS_TABELA)].rename(columns=COLUNAS_TABELA),
        width="stretch",
        hide_index=True,
        column_config={"Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY")},
    )
