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
    # Cálculos robustos
    media_global = df_aluno['Média Final'].mean()
    
    # Filtra por categoria (Comum/Técnico)
    m_comum = df_aluno[df_aluno['Categoria'] == 'Comum']['Média Final'].mean()
    m_tecnico = df_aluno[df_aluno['Categoria'] == 'Técnico']['Média Final'].mean()
    
    # Busca nota de Matemática específica
    nota_mat_df = df_aluno[df_aluno['Disciplina'].str.contains('Matemática', case=False)]
    nota_mat = nota_mat_df['Média Final'].values[0] if not nota_mat_df.empty else 0

    # Exibição conforme o desenho
    st.write(f"**Média núcleo comum:** {m_comum:.1f}")
    st.write(f"**Média núcleo técnico:** {m_tecnico:.1f}")
    st.write(f"**Média matemática:** {nota_mat:.1f}")
    st.divider()
    st.subheader(f"Média Global: {media_global:.1f}")

with m4:
    st.write("### Observações")
    # Botão de "+" discreto para novas caixas
    if st.button("+", help="Adicionar nova caixa"):
        st.session_state.caixas_obs += 1
    
    with st.form("form_save"):
        obs_lista = []
        # Puxa o que já existe na planilha para a primeira caixa
        obs_original = str(df_mat['Observações']) if pd.notna(df_mat['Observações']) else ""
        
        for i in range(st.session_state.caixas_obs):
            # Só preenche a primeira caixa com o dado da planilha para não repetir texto nas novas
            txt = st.text_area(f"Nota {i+1}", value=obs_original if i == 0 else "", key=f"area_{i}")
            obs_lista.append(txt)
            
        if st.form_submit_button("SALVAR NA PLANILHA"):
            # Junta os textos e atualiza
            texto_final = " | ".join([n for n in obs_lista if n.strip()])
            df.loc[(df['Aluno'] == aluno_nome) & (df['Disciplina'] == materia_graf), 'Observações'] = texto_final
            conn.update(data=df)
            st.success("Gravado!")

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
