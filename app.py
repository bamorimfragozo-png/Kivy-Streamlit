import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração e Estilo Visual (CSS Customizado)
st.set_page_config(page_title="Dashboard Escolar Profissional", layout="wide")

st.markdown("""
    <style>
    /* Estilização dos quadros pretos do desenho */
    [data-testid="stColumn"] {
        border: 2px solid black !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
    }
    /* Bolinhas de rádio fora do quadro */
    .stRadio > div { flex-direction: row; gap: 20px; }
    /* Ajuste para botões e inputs */
    .stButton>button { border: 1px solid black !important; border-radius: 5px; }
    .stTextArea textarea { border: 1px solid #ccc !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão e Dados
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")
df.columns = df.columns.str.strip()

# 3. Estados de Sessão (Interatividade)
if 'num_caixas' not in st.session_state: st.session_state.num_caixas = 1
if 'aluno_idx' not in st.session_state: st.session_state.aluno_idx = 0

# --- LÓGICA DE SELEÇÃO DE ALUNO (SETAS E NÚMERO DA CHAMADA) ---
col_nav_1, col_nav_2, col_nav_3 = st.columns([1, 2, 1])

with col_nav_2:
    # O quadrado do meio permite escolher o número/ID do aluno
    lista_indices = list(range(len(df['Aluno'].unique())))
    escolha_id = st.selectbox("Número do Aluno na Chamada:", options=lista_indices, 
                              index=st.session_state.aluno_idx, format_func=lambda x: f"Nº {x+1}")
    st.session_state.aluno_idx = escolha_id

# Navegação por setas (fora dos quadros principais)
bn1, bn2, bn3, bn4, bn5 = st.columns([4, 1, 1, 1, 4])
with bn2:
    if st.button("⬅️"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx - 1) % len(df['Aluno'].unique())
        st.rerun()
with bn4:
    if st.button("➡️"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx + 1) % len(df['Aluno'].unique())
        st.rerun()

# Definindo o aluno ativo
aluno_nome = df['Aluno'].unique()[st.session_state.aluno_idx]
df_aluno = df[df['Aluno'] == aluno_nome].copy()

# --- TOPO: FOTO | INFO ---
st.write("") # Espaçador
t1, t2 = st.columns([1, 4])
with t1:
    st.markdown("### Foto")
    st.image("https://via.placeholder.com/150", use_container_width=True)
with t2:
    st.subheader(f"Nome: {aluno_nome}")
    st.write(f"**Matrícula:** {df_aluno['Matrícula'].iloc[0]}")
    st.write(f"**Série:** {df_aluno['Série'].iloc[0]}")

# --- MEIO: DISCIPLINAS | GRÁFICOS | GLOBAL | OBSERVAÇÕES ---
# Bolinhas (Radio) FORA do quadrado das disciplinas
c_ordem = st.radio("Disciplinas ordenadas por menor nota/frequência:", ["Nota", "Frequência"], horizontal=True)

m1, m2, m3, m4 = st.columns([2, 3, 2, 2])

with m1:
    st.write("### Disciplinas")
    col_ref = 'Média Final' if c_ordem == "Nota" else 'Frequência'
    # Mostra todas as disciplinas ordenadas (menor para maior)
    df_sorted = df_aluno.sort_values(by=col_ref, ascending=True)
    st.table(df_sorted[['Disciplina', col_ref]])

with m2:
    # Retângulo de escolha de disciplina DENTRO do quadro de gráficos
    mat_escolhida = st.selectbox("Escolha a Disciplina para o Gráfico:", df_aluno['Disciplina'].unique())
    df_mat = df_aluno[df_aluno['Disciplina'] == mat_escolhida].iloc[0]
    
    # Gráfico 1: Notas
    fig1 = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI', 'Final'], 
                  y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI'], df_mat['Final']],
                  markers=True, title=f"Evolução: {mat_escolhida}")
    st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico 2: Frequência Geral (Ajustado: mostra o valor fixo da planilha)
    fig2 = px.bar(x=["Frequência Atual"], y=[df_mat['Frequência']], 
                  range_y=[0, 100], title="Frequência Geral (%)")
    st.plotly_chart(fig2, use_container_width=True)

with m3:
    st.write("### Global")
    st.metric("Média Global", f"{df_aluno['Média Final'].mean():.1f}")
    st.write("---")
    # Médias por núcleo
    if 'Categoria' in df_aluno.columns:
        st.write(f"**Núcleo Comum:** {df_aluno[df_aluno['Categoria']=='Comum']['Média Final'].mean():.1f}")
        st.write(f"**Núcleo Técnico:** {df_aluno[df_aluno['Categoria']=='Técnico']['Média Final'].mean():.1f}")
    
    # Nota de matemática específica
    nota_mat = df_aluno[df_aluno['Disciplina'] == 'Matemática']['Média Final'].values
    st.write(f"**Matemática:** {nota_mat[0] if len(nota_mat) > 0 else 'N/A'}")

with m4:
    st.write("### Observações")
    # Botão "+" discreto (estilo tabela antiga)
    if st.button("➕", help="Adicionar nova caixa de observação"):
        st.session_state.num_caixas += 1
    
    with st.form("salvar_obs"):
        novas_obs = []
        # Carrega observação existente na primeira caixa
        obs_original = str(df_mat['Observações']) if pd.notna(df_mat['Observações']) else ""
        
        for i in range(st.session_state.num_caixas):
            txt = st.text_area(f"Nota {i+1}", value=obs_original if i == 0 else "", key=f"obs_{i}")
            novas_obs.append(txt)
            
        if st.form_submit_button("SALVAR ALTERAÇÕES NA PLANILHA"):
            texto_final = " | ".join([n for n in novas_obs if n.strip()])
            # Localiza a linha correta e atualiza
            df.loc[(df['Aluno'] == aluno_nome) & (df['Disciplina'] == mat_escolhida), 'Observações'] = texto_final
            conn.update(data=df)
            st.success("Salvo!")
