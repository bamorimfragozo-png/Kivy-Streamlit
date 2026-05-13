import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração de Página e Estilo Visual (CSS)
st.set_page_config(page_title="Dashboard Escolar", layout="wide")

st.markdown("""
    <style>
    /* Força os blocos a terem borda preta arredondada igual ao desenho */
    [data-testid="stColumn"] {
        border: 2px solid black !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
        margin: 5px !important;
    }
    .stTextArea textarea { border: 1px solid black !important; }
    .stButton>button { border: 1px solid black !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão com Dados
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")
df.columns = df.columns.str.strip()

# 3. Gestão de Estado (Navegação e Observações Dinâmicas)
if 'aluno_index' not in st.session_state: st.session_state.aluno_index = 0
if 'caixas_obs' not in st.session_state: st.session_state.caixas_obs = 1

# Filtro de Aluno
alunos = df['Aluno'].unique().tolist()
nome_aluno = alunos[st.session_state.aluno_index]
df_aluno = df[df['Aluno'] == nome_aluno].copy()

# --- TOPO: IDENTIFICAÇÃO ---
col_foto, col_dados = st.columns([1, 4])
with col_foto:
    st.write("**Foto**")
    st.image("https://via.placeholder.com/150", use_container_width=True)

with col_dados:
    st.subheader(f"Aluno: {nome_aluno}")
    c1, c2 = st.columns(2)
    c1.write(f"**Matrícula:** {df_aluno['Matrícula'].iloc[0]}")
    c2.write(f"**Série:** {df_aluno['Série'].iloc[0]}")

st.divider()

# --- CORPO: DISCIPLINAS | GRÁFICOS | GLOBAL | OBSERVAÇÕES ---
c_disc, c_graf, c_glob, c_obs = st.columns([1.5, 3, 1.5, 1.5])

with c_disc:
    st.write("### Disciplinas")
    ordem = st.radio("Ordenar menor por:", ["Nota", "Frequência"])
    col_ref = 'Média Final' if ordem == "Nota" else 'Frequência'
    
    df_sorted = df_aluno.sort_values(by=col_ref, ascending=True)
    
    # Lista de matérias como botões (Retângulos)
    for m in df_sorted['Disciplina'].unique():
        if st.button(f"{m} ({df_sorted[df_sorted['Disciplina']==m][col_ref].values[0]})"):
            st.session_state.materia_atual = m

if 'materia_atual' not in st.session_state:
    st.session_state.materia_atual = df_aluno['Disciplina'].iloc[0]

df_mat = df_aluno[df_aluno['Disciplina'] == st.session_state.materia_atual].iloc[0]

with c_graf:
    st.write(f"### Gráficos: {st.session_state.materia_atual}")
    # Gráfico 1: Notas
    fig1 = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI', 'Final'], 
                  y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI'], df_mat['Final']],
                  markers=True, title="Evolução de Notas")
    st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico 2: Frequência
    fig2 = px.bar(x=['Jan', 'Fev', 'Mar', 'Abr'], y=[85, 90, 75, 95], title="Frequência Mensal (%)")
    st.plotly_chart(fig2, use_container_width=True)

with c_glob:
    st.write("### Global")
    st.metric("Média Global", f"{df_aluno['Média Final'].mean():.1f}")
    if 'Categoria' in df_aluno.columns:
        st.write(f"Núcleo Comum: {df_aluno[df_aluno['Categoria']=='Comum']['Média Final'].mean():.1f}")
        st.write(f"Núcleo Técnico: {df_aluno[df_aluno['Categoria']=='Técnico']['Média Final'].mean():.1f}")

with c_obs:
    st.write("### Observações +")
    if st.button("➕"):
        st.session_state.caixas_obs += 1
    
    with st.form("form_observacoes"):
        lista_notas = []
        for i in range(st.session_state.caixas_obs):
            # Tenta puxar obs existente apenas na primeira caixa
            val_padrao = df_mat['Observações'] if i == 0 and pd.notna(df_mat['Observações']) else ""
            txt = st.text_area(f"Nota {i+1}", value=val_padrao, key=f"area_{i}")
            lista_notas.append(txt)
        
        if st.form_submit_button("Salvar na Planilha"):
            obs_unida = " | ".join([n for n in lista_notas if n])
            # Atualiza o DataFrame e envia para o Google
            df.loc[(df['Aluno'] == nome_aluno) & (df['Disciplina'] == st.session_state.materia_atual), 'Observações'] = obs_unida
            conn.update(data=df)
            st.success("Dados salvos!")

# --- RODAPÉ: NAVEGAÇÃO ---
st.divider()
b_voltar, b_meio, b_frente = st.columns([1, 4, 1])
with b_voltar:
    if st.button("⬅️ Anterior"):
        st.session_state.aluno_index = (st.session_state.aluno_index - 1) % len(alunos)
        st.rerun()
with b_frente:
    if st.button("Próximo ➡️"):
        st.session_state.aluno_index = (st.session_state.aluno_index + 1) % len(alunos)
        st.rerun()
