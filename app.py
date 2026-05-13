import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração e Estilo (Cantos arredondados e bordas pretas)
st.set_page_config(page_title="Dashboard Acadêmico", layout="wide")

st.markdown("""
    <style>
    [data-testid="stColumn"] {
        border: 2px solid black !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
    }
    .stTextArea textarea { border: 1px solid black !important; }
    .stButton>button { border: 1px solid black !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para garantir leitura sempre fresca
def load_data():
    data = conn.read(ttl="0")
    data.columns = data.columns.str.strip()
    return data

df = load_data()

# 3. Inicialização de Estados (Não perde dados ao clicar)
if 'aluno_idx' not in st.session_state: st.session_state.aluno_idx = 0
if 'caixas' not in st.session_state: st.session_state.caixas = 1

# Filtro de Aluno baseado no Índice da Seta
alunos = df['Aluno'].unique().tolist()
total_alunos = len(alunos)
aluno_nome = alunos[st.session_state.aluno_idx]
df_aluno = df[df['Aluno'] == aluno_nome].copy()

# --- TOPO: FOTO | DADOS DO ALUNO ---
col_foto, col_topo = st.columns([1, 4])

with col_foto:
    st.write("**Foto**")
    st.image("https://via.placeholder.com/150", use_container_width=True)

with col_topo:
    st.subheader(f"Aluno: {aluno_nome}")
    c1, c2 = st.columns(2)
    c1.write(f"**Matrícula:** {df_aluno['Matrícula'].iloc[0]}")
    c2.write(f"**Série:** {df_aluno['Série'].iloc[0]}")

st.divider()

# --- CORPO: DISCIPLINAS | GRÁFICOS | GLOBAL | OBSERVAÇÕES ---
c_disc, c_graf, c_glob, c_obs = st.columns([1.5, 3, 1.5, 1.5])

with c_disc:
    st.write("### Disciplinas")
    ordem = st.radio("Ordenar menor por:", ["Nota", "Frequência"])
    col_ordem = 'Média Final' if ordem == "Nota" else 'Frequência'
    
    # Ordenação: Menor valor no topo (exatamente como pedido)
    df_lista = df_aluno.sort_values(by=col_ordem, ascending=True)
    
    # Seleção por "Clique" (selectbox que atua como gatilho)
    materia_sel = st.selectbox("Selecione a Matéria:", df_lista['Disciplina'].unique())
    df_mat = df_aluno[df_aluno['Disciplina'] == materia_sel].iloc[0]

with c_graf:
    st.write(f"### Dash: {materia_sel}")
    # Gráfico 1: Notas
    fig1 = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI', 'Final'], 
                  y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI'], df_mat['Final']],
                  markers=True, title="Evolução de Notas")
    fig1.update_yaxes(range=[0, 10])
    st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico 2: Frequência (Barras)
    fig2 = px.bar(x=['Jan', 'Fev', 'Mar', 'Abr'], y=[80, 90, 70, 95], title="Frequência por Mês (%)")
    st.plotly_chart(fig2, use_container_width=True)

with c_glob:
    st.write("### Global")
    # Resumo do Aluno (Médias de todos os registros dele)
    st.metric("Média Global", f"{df_aluno['Média Final'].mean():.1f}")
    if 'Categoria' in df_aluno.columns:
        tec = df_aluno[df_aluno['Categoria'] == 'Técnico']['Média Final'].mean()
        com = df_aluno[df_aluno['Categoria'] == 'Comum']['Média Final'].mean()
        st.write(f"**Núcleo Técnico:** {tec:.1f}")
        st.write(f"**Núcleo Comum:** {com:.1f}")
    
    # Média de Matemática específica desse aluno
    nota_mat = df_aluno[df_aluno['Disciplina'] == 'Matemática']['Média Final'].values
    st.write(f"**Matemática:** {nota_mat[0] if len(nota_mat) > 0 else 'N/A'}")

with c_obs:
    st.write("### Observações +")
    # Botão Interativo que soma caixas
    if st.button("➕"):
        st.session_state.caixas += 1
    
    with st.form("form_update"):
        textos = []
        # Carrega o que já existe na planilha para a primeira caixa
        obs_original = str(df_mat['Observações']) if pd.notna(df_mat['Observações']) else ""
        
        for i in range(st.session_state.caixas):
            t = st.text_area(f"Nota {i+1}", value=obs_original if i == 0 else "", key=f"txt_{i}")
            textos.append(t)
        
        if st.form_submit_button("Salvar na Planilha"):
            obs_unida = " | ".join([x for x in textos if x.strip()])
            # Procura a linha exata e atualiza no DataFrame mestre
            df.loc[(df['Aluno'] == aluno_nome) & (df['Disciplina'] == materia_sel), 'Observações'] = obs_unida
            # Envia o DataFrame inteiro de volta para o Google Sheets
            conn.update(data=df)
            st.success("Salvo com sucesso!")

# --- RODAPÉ: SETAS DE NAVEGAÇÃO ---
st.divider()
b_voltar, b_vazio, b_avancar = st.columns([1, 4, 1])

with b_voltar:
    if st.button("⬅️ Aluno Anterior"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx - 1) % total_alunos
        st.session_state.caixas = 1 # Reseta caixas ao trocar aluno
        st.rerun()

with b_avancar:
    if st.button("Próximo Aluno ➡️"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx + 1) % total_alunos
        st.session_state.caixas = 1 # Reseta caixas ao trocar aluno
        st.rerun()
