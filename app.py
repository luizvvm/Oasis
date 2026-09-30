import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard de Acidentes - RJ", layout="wide")

st.title("Painel de Análise e Corredores Rodoviários no Rio de Janeiro")
st.write("Análise detalhada de acidentes nas rodovias federais do Estado do Rio de Janeiro.")

# 1. Carregar e garantir colunas necessárias
@st.cache_data
def load_data():
    df = pd.read_csv('datatran2026_rj.csv')
    # Garantir que a coluna hora exista
    if 'hora' not in df.columns:
        df['hora'] = pd.to_datetime(df['horario'], format='%H:%M:%S', errors='coerce').dt.hour
    return df

df_rj = load_data()

# Sidebar para filtros
st.sidebar.header("Filtros de Pesquisa")
corredores_disponiveis = sorted(df_rj['nome_corredor'].dropna().unique().tolist())
corredores_selecionados = st.sidebar.multiselect(
    "Selecione as Rodovias (BRs):",
    options=corredores_disponiveis,
    default=corredores_disponiveis
)

# Filtrar base de dados
df_filtrado = df_rj[df_rj['nome_corredor'].isin(corredores_selecionados)].copy()

# 2. Resumo de Métricas Principais
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Ocorrências", len(df_filtrado))
col2.metric("Vítimas Fatais", int(df_filtrado['mortos'].sum()))
col3.metric("Feridos Graves", int(df_filtrado['feridos_graves'].sum()))
col4.metric("Feridos Leves", int(df_filtrado['feridos_leves'].sum()))

st.markdown("---")

# 3. Organização do Dashboard em Abas
tab_mapa, tab_temporal, tab_causas, tab_via = st.tabs([
    "Visão Geral & Mapa",
    "Análise Temporal",
    "Causas & Severidade",
    "Infraestrutura & Clima"
])


# ABA 1: MAPA GEOGRÁFICO
with tab_mapa:
    st.subheader("Mapeamento Geográfico dos Incidentes")

    layer_acidentes = pdk.Layer(
        "ScatterplotLayer",
        data=df_filtrado,
        get_position=["longitude", "latitude"],
        get_color="[220, 50, 50, 160]",
        get_radius=250,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=-22.5,
        longitude=-43.2,
        zoom=7,
        pitch=30
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer_acidentes],
            initial_view_state=view_state,
            tooltip={"text": "BR: {nome_corredor}\nKM: {km}\nMunicípio: {municipio}\nTipo: {tipo_acidente}"}
        )
    )


# ABA 2: ANÁLISE TEMPORAL
with tab_temporal:
    st.subheader("Distribuição por Horário e Calendário")
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("**Ocorrências por Horário do Dia (0h - 23h)**")
        contagem_hora = df_filtrado.groupby('hora').size().reset_index(name='quantidade')
        fig_hora = px.bar(contagem_hora, x='hora', y='quantidade', labels={'hora': 'Hora do Dia', 'quantidade': 'Ocorrências'}, color_discrete_sequence=['#1f77b4'])
        st.plotly_chart(fig_hora, use_container_width=True)

    with col_t2:
        st.markdown("**Ocorrências por Dia da Semana**")
        dias_ordem = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
        contagem_dia = df_filtrado['dia_semana'].value_counts().reindex(dias_ordem).reset_index()
        contagem_dia.columns = ['dia_semana', 'quantidade']
        fig_dia = px.bar(contagem_dia, x='dia_semana', y='quantidade', labels={'dia_semana': 'Dia', 'quantidade': 'Ocorrências'}, color_discrete_sequence=['#2ca02c'])
        st.plotly_chart(fig_dia, use_container_width=True)

    st.markdown("**Ocorrências por Fase do Dia**")
    fase_dia = df_filtrado['fase_dia'].value_counts().reset_index()
    fase_dia.columns = ['fase_dia', 'quantidade']
    fig_fase = px.bar(fase_dia, x='fase_dia', y='quantidade', labels={'fase_dia': 'Fase', 'quantidade': 'Quantidade'}, color_discrete_sequence=['#9467bd'])
    st.plotly_chart(fig_fase, use_container_width=True)


# ABA 3: CAUSAS E SEVERIDADE
with tab_causas:
    st.subheader("Perfi dos Acidentes e Severidade")
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("**Principais Tipos de Acidentes**")
        top_tipos = df_filtrado['tipo_acidente'].value_counts().head(8).reset_index()
        top_tipos.columns = ['tipo_acidente', 'quantidade']
        fig_tipo = px.bar(top_tipos, y='tipo_acidente', x='quantidade', orientation='h', labels={'tipo_acidente': 'Tipo', 'quantidade': 'Total'}, color_discrete_sequence=['#ff7f0e'])
        fig_tipo.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_tipo, use_container_width=True)

    with col_c2:
        st.markdown("**Classificação por Severidade**")
        classificacao = df_filtrado['classificacao_acidente'].value_counts().reset_index()
        classificacao.columns = ['classificacao', 'quantidade']
        fig_class = px.pie(classificacao, names='classificacao', values='quantidade', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_class, use_container_width=True)

    st.markdown("**Top 10 Principais Causas**")
    top_causas = df_filtrado['causa_acidente'].value_counts().head(10).reset_index()
    top_causas.columns = ['Causa do Acidente', 'Total de Ocorrências']
    st.dataframe(top_causas, use_container_width=True)

# ABA 4: INFRAESTRUTURA E CLIMA
with tab_via:
    st.subheader("Influência da Infraestrutura e Condições Meteorológicas")
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        st.markdown("**Condições Meteorológicas**")
        clima = df_filtrado['condicao_metereologica'].value_counts().reset_index()
        clima.columns = ['condicao', 'quantidade']
        fig_clima = px.bar(clima, x='condicao', y='quantidade', labels={'condicao': 'Clima', 'quantidade': 'Ocorrências'}, color_discrete_sequence=['#17becf'])
        st.plotly_chart(fig_clima, use_container_width=True)

    with col_v2:
        st.markdown("**Tipo de Pista e Traçado da Via**")
        tracado = df_filtrado['tracado_via'].value_counts().head(6).reset_index()
        tracado.columns = ['tracado', 'quantidade']
        fig_tracado = px.bar(tracado, y='tracado', x='quantidade', orientation='h', labels={'tracado': 'Traçado', 'quantidade': 'Total'}, color_discrete_sequence=['#8c564b'])
        fig_tracado.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_tracado, use_container_width=True)

    st.markdown("**Municípios do RJ com Maior Volume de Ocorrências**")
    top_mun = df_filtrado['municipio'].value_counts().head(10).reset_index()
    top_mun.columns = ['Município', 'Total de Acidentes']
    st.dataframe(top_mun, use_container_width=True)

# Exibição da tabela bruta de dados
with st.expander("Exibir base de dados bruta em tabela"):
    st.dataframe(df_filtrado[['data_inversa', 'horario', 'nome_corredor', 'km', 'municipio', 'tipo_acidente', 'classificacao_acidente', 'causa_acidente', 'mortos', 'feridos']])