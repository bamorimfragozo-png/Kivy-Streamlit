import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração e Estilo (Bordas pretas de 2px e cantos arredondados)
st.set_page_config(page_title="Dashboard Acadêmico", layout="wide")

st.markdown("""
    <style>
    [data-testid="stColumn"] {
        border: 2px solid black !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
        margin-bottom: 10px;
    }
    .stRadio > div { flex-direction: row; gap: 20px; }
    .stTextArea textarea { border: 1px solid #333 !important; }
    .stButton>button { border: 1px solid black !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão e Carregamento
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    data = conn.read(ttl="0")
    data.columns = data.columns.str.strip()
    return data

df = load_data()
alunos_unicos = df['Aluno'].unique().tolist()

# 3. Estados de Sessão (Persistência)
if 'aluno_idx' not in st.session_state: st.session_state.aluno_idx = 0
if 'caixas_obs' not in st.session_state: st.session_state.caixas_obs = 1

# --- TOPO: IDENTIFICAÇÃO ---
aluno_nome = alunos_unicos[st.session_state.aluno_idx]
df_aluno = df[df['Aluno'] == aluno_nome].copy()

t1, t2 = st.columns([1, 4])
with t1:
    st.markdown("### Foto")
    st.image("https://via.placeholder.com/150", use_container_width=True)
with t2:
    st.subheader(f"Nome: {aluno_nome}")
    c1, c2 = st.columns(2)
    c1.write(f"**Matrícula:** {df_aluno['Matrícula'].iloc[0]}")
    c2.write(f"**Série:** {df_aluno['Série'].iloc[0]}")

st.divider()

# --- MEIO: DISCIPLINAS | GRÁFICOS | GLOBAL | OBSERVAÇÕES ---
# Opções de ordenação FORA dos quadros
c_ordem = st.radio("Ordenar disciplinas por menor:", ["Nota", "Frequência"], horizontal=True)

m1, m2, m3, m4 = st.columns([2, 3, 2, 2])

with m1:
    st.write("### Disciplinas")
    col_ref = 'Média Final' if c_ordem == "Nota" else 'Frequência'
    df_sorted = df_aluno.sort_values(by=col_ref, ascending=True)
    st.table(df_sorted[['Disciplina', col_ref]])

with m2:
    # Seletor de matéria DENTRO do quadro de gráficos
    materia_graf = st.selectbox("Escolha a Disciplina:", df_aluno['Disciplina'].unique())
    df_mat = df_aluno[df_aluno['Disciplina'] == materia_graf].iloc[0]
    
    # Gráfico 1: Notas
    fig1 = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI', 'Final'], 
                  y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI'], df_mat['Final']],
                  markers=True, title=f"Evolução: {materia_graf}")
    fig1.update_yaxes(range=[0, 10])
    st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico 2: Frequência
    fig2 = px.bar(x=["Frequência"], y=[df_mat['Frequência']], range_y=[0, 100], title="Frequência Geral (%)")
    st.plotly_chart(fig2, use_container_width=True)

with m3:
    st.write("### Global")
    # Cálculos das médias conforme o print
    media_global = df_aluno['Média Final'].mean()
    media_comum = df_aluno[df_aluno['Categoria'] == 'Comum']['Média Final'].mean()
    media_tecnico = df_aluno[df_aluno['Categoria'] == 'Técnico']['Média Final'].mean()
    nota_mat = df_aluno[df_aluno['Disciplina'] == 'Matemática']['Média Final'].values[0]

    st.write(f"**Média do aluno núcleo comum:** {media_comum:.2f}")
    st.write(f"**Média do aluno núcleo técnico:** {media_tecnico:.2f}")
    st.write(f"**Média do aluno matemática:** {nota_mat:.2f}")
    st.write("---")
    st.subheader(f"Média global: {media_global:.1f}")

with m4:
    st.write("### Observações")
    # Botão discreto estilo tabela antiga
    if st.button("➕", help="Adicionar nova nota"):
        st.session_state.num_caixas += 1

    with st.form("form_notas"):
        lista_final = []
        # Puxa o que já existe na planilha para a primeira caixa
        obs_banco = str(df_mat['Observações']) if pd.notna(df_mat['Observações']) else ""
        
        for i in range(st.session_state.num_caixas):
            txt = st.text_area(f"Nota {i+1}", value=obs_banco if i == 0 else "", key=f"obs_input_{i}")
            lista_final.append(txt)
            
        if st.form_submit_button("SALVAR ALTERAÇÕES NA PLANILHA"):
            texto_unificado = " | ".join([n for n in lista_final if n.strip()])
            # Procura a linha certa (Aluno + Matéria) e grava
            df.loc[(df['Aluno'] == aluno_nome) & (df['Disciplina'] == mat_escolhida), 'Observações'] = texto_unificado
            conn.update(data=df) # Comando que envia de volta para a planilha
            st.success("Salvo com sucesso!")

# --- RODAPÉ: NAVEGAÇÃO COM SETAS E NÚMERO ---
st.divider()
b1, b2, b3 = st.columns([1, 2, 1])

with b1:
    if st.button("⬅️ Anterior"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx - 1) % len(alunos_unicos)
        st.rerun()

with b2:
    # Quadrado central com número da chamada
    n_chamada = st.selectbox("Número do Aluno:", options=range(len(alunos_unicos)), 
                             index=st.session_state.aluno_idx, 
                             format_func=lambda x: f"Nº {x+1}")
    if n_chamada != st.session_state.aluno_idx:
        st.session_state.aluno_idx = n_chamada
        st.rerun()

with b3:
    if st.button("Próximo ➡️"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx + 1) % len(alunos_unicos)
        st.rerun()
