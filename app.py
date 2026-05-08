import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração da Página
st.set_page_config(page_title="Dashboard Escolar", layout="wide")

# 2. Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="1m")

# Limpeza básica: remove espaços extras dos nomes das colunas
df.columns = df.columns.str.strip()

# --- CABEÇALHO ---
col_foto, col_info = st.columns([1, 4])

with col_foto:
    st.image("https://via.placeholder.com/150", caption="Foto do Aluno")

with col_info:
    lista_alunos = df['Aluno'].unique()
    aluno_selecionado = st.selectbox("👤 Escolha o Aluno:", lista_alunos)
    df_aluno = df[df['Aluno'] == aluno_selecionado].copy()
    
    # Preenchimento das informações do topo
    # Usamos .get() para evitar o erro de KeyError se a coluna sumir
    serie = df_aluno['Série'].iloc[0] if 'Série' in df_aluno.columns else "N/A"
    st.write(f"**Nome:** {aluno_selecionado}")
    st.write(f"**Série:** {serie}")

# --- CORPO DO DASHBOARD ---
col_disc, col_graficos, col_global, col_obs = st.columns([2, 3, 1.5, 1.5])

with col_disc:
    st.markdown("### Disciplinas")
    # AQUI ESTÁ A LÓGICA DE ORDENAÇÃO QUE VOCÊ PEDIU
    criterio = st.radio("Ordenar por:", ["Nota", "Frequência"])
    
    coluna_ordem = 'Média Final' if criterio == "Nota" else 'Frequência'
    
    if coluna_ordem in df_aluno.columns:
        # Ordena: Menor valor no topo, maior valor embaixo
        df_aluno = df_aluno.sort_values(by=coluna_ordem, ascending=True)
    
    lista_matérias = df_aluno['Disciplina'].unique()
    materia_selecionada = st.radio("Selecione a Matéria:", lista_matérias)
    df_final = df_aluno[df_aluno['Disciplina'] == materia_selecionada]

with col_graficos:
    st.markdown(f"### Gráficos: {materia_selecionada}")
    
    if criterio == "Nota":
        # Gráfico de Evolução de Notas (Linha)
        bimestres = ['1º BI', '2º BI', '3º BI', '4º BI']
        notas = [df_final[b].values[0] for b in bimestres if b in df_final.columns]
        fig = px.line(x=bimestres, y=notas, markers=True, title="Evolução das Notas")
        fig.update_yaxes(range=[0, 10])
    else:
        # Gráfico de Frequência (Barras)
        # Exemplo: se você tiver colunas de meses na planilha
        meses = ["Jan", "Fev", "Mar"] 
        # Aqui você pode adaptar para as colunas de frequência mensal da sua planilha
        fig = px.bar(x=meses, y=[8, 9, 7], title="Frequência por Período")
    
    st.plotly_chart(fig, use_container_width=True)

with col_global:
    st.markdown("### Global")
    media_geral = df_aluno['Média Final'].mean() if 'Média Final' in df_aluno.columns else 0
    st.metric("Média Geral", f"{media_geral:.1f}")
    
    if 'Frequência' in df_final.columns:
        st.metric("Freq. da Disciplina", f"{df_final['Frequência'].values[0]}")

with col_obs:
    st.markdown("### Observações +")
    obs = df_final['Observações'].values[0] if 'Observações' in df_final.columns else "Sem obs."
    st.info(obs)
