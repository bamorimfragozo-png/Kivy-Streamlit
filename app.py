import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração da Página
st.set_page_config(page_title="Dashboard Escolar", layout="wide")

# 2. Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="1m")

# 3. CSS para fazer os quadros pretos arredondados do seu desenho
st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > div:has(div.stColumn) > div.stColumn {
        border: 2px solid black;
        border-radius: 15px;
        padding: 20px;
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO ---
col_foto, col_info = st.columns([1, 4])

with col_foto:
    st.markdown("### Foto")
    st.image("https://via.placeholder.com/150", caption="Foto do Aluno")

with col_info:
    lista_alunos = df['Aluno'].unique()
    aluno_selecionado = st.selectbox("👤 Escolha o Aluno:", lista_alunos)
    df_aluno = df[df['Aluno'] == aluno_selecionado]
    
    c1, c2 = st.columns(2)
    c1.write(f"**Nome:** {aluno_selecionado}")
    c2.write(f"**Série:** {df_aluno['Série'].iloc[0]}")

st.write("") # Espaçador

# --- CORPO DO DASHBOARD ---
col_disc, col_graficos, col_global, col_obs = st.columns([1.5, 3, 1.5, 1.5])

with col_disc:
    st.markdown("### Disciplinas")
    ordem = st.radio("Ordenar por:", ["Nota", "Frequência"])
    # Filtra as matérias do aluno selecionado
    lista_matérias = df_aluno['Disciplina'].unique()
    materia_selecionada = st.radio("Selecione a Matéria:", lista_matérias)
    df_final = df_aluno[df_aluno['Disciplina'] == materia_selecionada]

with col_graficos:
    st.markdown(f"### Gráficos: {materia_selecionada}")
    # Gráfico de Evolução (Linha)
    bimestres = ['1º BI', '2º BI', '3º BI', '4º BI']
    notas = [df_final['1º BI'].values[0], df_final['2º BI'].values[0], 
             df_final['3º BI'].values[0], df_final['4º BI'].values[0]]
    
    fig_linha = px.line(x=bimestres, y=notas, markers=True, title="Evolução Bimestral")
    fig_linha.update_yaxes(range=[0, 10])
    st.plotly_chart(fig_linha, use_container_width=True)
    
    # Gráfico de Barras (Meses)
    fig_barras = px.bar(x=["Jan", "Fev", "Mar"], y=[8, 9, 7], title="Frequência Mensal")
    st.plotly_chart(fig_barras, use_container_width=True)

with col_global:
    st.markdown("### Global")
    st.metric("Média Geral", f"{df_aluno['Média Final'].mean():.1f}")
    st.metric("Freq. Global", df_final['Frequência'].values[0])
    st.metric("Matemática", "7.5") # Exemplo estático

with col_obs:
    st.markdown("### Observações +")
    st.info(df_final['Observações'].values[0])
