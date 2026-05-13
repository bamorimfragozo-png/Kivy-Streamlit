import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configurações e Estilo Visual (Bordas pretas arredondadas conforme o desenho)
st.set_page_config(page_title="Dashboard Acadêmico", layout="wide")

st.markdown("""
    <style>
    /* Estilo para simular os quadros pretos do desenho */
    [data-testid="stColumn"] {
        border: 2px solid black !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
        margin-bottom: 10px;
    }
    .stRadio > div { flex-direction: row; gap: 20px; margin-bottom: -10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão e Dados
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")
df.columns = df.columns.str.strip()

# Garantir que observações aceite texto
if 'Observações' in df.columns:
    df['Observações'] = df['Observações'].astype(str).replace('nan', '')

# Estados de Navegação
if 'aluno_idx' not in st.session_state: st.session_state.aluno_idx = 0
alunos_lista = df['Aluno'].unique().tolist()
aluno_atual = alunos_lista[st.session_state.aluno_idx]
df_aluno = df[df['Aluno'] == aluno_atual].copy()

# --- TOPO: IDENTIFICAÇÃO ---
t1, t2 = st.columns([1, 4])
with t1:
    st.markdown("### Foto")
    st.image("https://via.placeholder.com/150", use_container_width=True)
with t2:
    st.subheader(f"Nome: {aluno_atual}")
    c1, c2 = st.columns(2)
    c1.write(f"**Matrícula:** {df_aluno['Matrícula'].iloc[0]}")
    c2.write(f"**Série:** {df_aluno['Série'].iloc[0]}")

# --- MIOLO DO DASHBOARD ---
# Opções de ordenação fora dos quadros
ordem = st.radio("Ordenar disciplinas por menor:", ["Nota", "Frequência"])

m1, m2, m3, m4 = st.columns([2, 3, 2, 2])

with m1:
    st.write("### Disciplinas")
    col_ref = 'Média Final' if ordem == "Nota" else 'Freq. Final'
    df_lista = df_aluno.sort_values(by=col_ref, ascending=True)
    
    # Seleção por clique na disciplina
    mat_selecionada = st.radio("Selecione para ver os gráficos:", df_lista['Disciplina'].unique(), label_visibility="collapsed")
    df_mat = df_aluno[df_aluno['Disciplina'] == mat_selecionada].iloc[0]

with m2:
    # QUADRO DE NOTAS
    st.write(f"**Evolução: {mat_selecionada}**")
    fig_n = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI'], 
                   y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI']], markers=True)
    fig_n.update_yaxes(range=[0, 10.5])
    fig_n.update_layout(height=200, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig_n, use_container_width=True)
    
    st.divider() # Divisor para separar os dois gráficos em sub-quadros
    
    # QUADRO DE FREQUÊNCIA MENSAL (%)
    st.write("**Frequência Mensal (%)**")
    meses = ['Freq. Jan.', 'Freq. Fev.', 'Freq. Mar.', 'Freq. Abr.', 'Freq. Mai.', 'Freq. Jun.', 
             'Freq. Jul.', 'Freq. Ago.', 'Freq. Set.', 'Freq. Out.', 'Freq. Nov.', 'Freq. Dez.']
    
    # Converte decimais da planilha (ex: 0.85) para porcentagem real (85%)
    valores_f = []
    for m in meses:
        val = df_mat[m]
        if isinstance(val, str): val = float(val.replace('%','').replace(',','.'))
        if val <= 1.0: val = val * 100 # Converte 0.85 para 85
        valores_f.append(val)
        
    fig_f = px.bar(x=[m.split('.')[1].strip() for m in meses], y=valores_f)
    fig_f.update_yaxes(range=[0, 105], title="%")
    fig_f.update_layout(height=200, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig_f, use_container_width=True)

with m3:
    st.write("### Global")
    m_comum = df_aluno[df_aluno['Núcleo'] == 'Comum']['Média Final'].mean()
    m_tec = df_aluno[df_aluno['Núcleo'] == 'Técnico']['Média Final'].mean()
    nota_mat = df_aluno[df_aluno['Disciplina'].str.contains('Matemática', case=False)]['Média Final'].values[0]
    
    st.write(f"Média Núcleo Comum: **{m_comum:.2f}**")
    st.write(f"Média Núcleo Técnico: **{m_tec:.2f}**")
    st.write(f"Média Matemática: **{nota_mat:.2f}**")
    st.divider()
    st.subheader(f"Média Global: {df_aluno['Média Final'].mean():.1f}")

with m4:
    st.write("### Observações +")
    with st.form("salvar_obs"):
        obs_atual = str(df_mat['Observações']) if pd.notna(df_mat['Observações']) else ""
        texto = st.text_area("Notas:", value=obs_atual, height=300)
        if st.form_submit_button("SALVAR NA PLANILHA"):
            idx = df[(df['Aluno'] == aluno_atual) & (df['Disciplina'] == mat_selecionada)].index
            df.at[idx[0], 'Observações'] = str(texto)
            conn.update(data=df)
            st.success("Salvo!")

# --- RODAPÉ: NAVEGAÇÃO POR NÚMERO ---
st.divider()
b1, b2, b3 = st.columns([1, 1, 1])
with b1:
    if st.button("⬅️ Anterior"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx - 1) % len(alunos_lista)
        st.rerun()
with b2:
    # Quadrado central com o número da chamada (conforme solicitado)
    num_escolha = st.selectbox("Aluno Nº:", options=range(len(alunos_lista)), 
                              index=st.session_state.aluno_idx,
                              format_func=lambda x: f"Nº {df[df['Aluno'] == alunos_lista[x]]['Nº Chamada'].iloc[0]}")
    if num_escolha != st.session_state.aluno_idx:
        st.session_state.aluno_idx = num_escolha
        st.rerun()
with b3:
    if st.button("Próximo ➡️"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx + 1) % len(alunos_lista)
        st.rerun()
