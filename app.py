import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração e Estilo CSS
st.set_page_config(page_title="Dashboard Escolar", layout="wide")

st.markdown("""
    <style>
    /* Estilo para simular os quadrados do desenho */
    [data-testid="stColumn"] {
        border: 2px solid black !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
        margin-bottom: 10px;
    }
    .stMetric { border: 1px solid #eee; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão e Tratamento de Dados
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")
df.columns = df.columns.str.strip()

# RESOLVE O TYPEERROR: Garante que Observações seja sempre texto
if 'Observações' in df.columns:
    df['Observações'] = df['Observações'].astype(str).replace('nan', '')

# Navegação de Alunos
if 'aluno_idx' not in st.session_state: st.session_state.aluno_idx = 0
alunos_lista = df['Aluno'].unique().tolist()
aluno_atual = alunos_lista[st.session_state.aluno_idx]
df_aluno = df[df['Aluno'] == aluno_atual].copy()

# --- TOPO: IDENTIFICAÇÃO ---
t1, t2 = st.columns([1, 4])
with t1:
    st.markdown("### Foto")
    st.image("https://via.placeholder.com/150") # Substituir pela URL real se houver
with t2:
    st.subheader(f"Aluno: {aluno_atual}")
    st.write(f"**Matrícula:** {df_aluno['Matrícula'].iloc[0]} | **Série:** {df_aluno['Série'].iloc[0]}")

# --- MIOLO DO DASHBOARD ---
m1, m2_notas, m2_freq, m3, m4 = st.columns([2, 3, 3, 2, 2])

# QUADRADO 1: Disciplinas (Seleção via Rádio para evitar erro de versão)
with m1:
    st.write("### Disciplinas")
    ordem = st.radio("Ordenar por:", ["Nota", "Frequência"], horizontal=True)
    col_sort = 'Média Final' if ordem == "Nota" else 'Freq. Final'
    
    # Lista de matérias ordenada
    materias_disp = df_aluno.sort_values(by=col_sort)['Disciplina'].tolist()
    mat_escolhida = st.radio("Selecione para ver detalhes:", materias_disp)
    
    st.divider()
    df_tab = df_aluno[['Disciplina', col_sort]].sort_values(by=col_sort)
    st.table(df_tab)

# QUADRADOS 2 e 3: Gráficos Separados
df_mat = df_aluno[df_aluno['Disciplina'] == mat_escolhida].iloc[0]

with m2_notas:
    st.write(f"### Evolução: {mat_escolhida}")
    fig_notas = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI'], 
                        y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI']],
                        markers=True)
    fig_notas.update_yaxes(range=[0, 10.5])
    st.plotly_chart(fig_notas, use_container_width=True)

with m2_freq:
    st.write("### Frequência Mensal (%)")
    meses_cols = ['Freq. Jan.', 'Freq. Fev.', 'Freq. Mar.', 'Freq. Abr.', 'Freq. Mai.', 'Freq. Jun.', 
                  'Freq. Jul.', 'Freq. Ago.', 'Freq. Set.', 'Freq. Out.', 'Freq. Nov.', 'Freq. Dez.']
    
    # Tratamento para garantir que vire número e vire porcentagem (0.85 -> 85)
    def to_percent(val):
        try:
            v = float(str(val).replace('%','').replace(',','.'))
            return v * 100 if v <= 1.0 else v
        except: return 0.0

    valores_f = [to_percent(df_mat[m]) for m in meses_cols]
    fig_freq = px.bar(x=[m.split('.')[1].strip() for m in meses_cols], y=valores_f)
    fig_freq.update_yaxes(range=[0, 105], title="%")
    st.plotly_chart(fig_freq, use_container_width=True)

# QUADRADO 3: Médias Globais
with m3:
    st.write("### Global")
    med_global = df_aluno['Média Final'].mean()
    med_comum = df_aluno[df_aluno['Núcleo'] == 'Comum']['Média Final'].mean()
    med_tec = df_aluno[df_aluno['Núcleo'] == 'Técnico']['Média Final'].mean()
    
    st.write(f"Núcleo Comum: **{med_comum:.1f}**")
    st.write(f"Núcleo Técnico: **{med_tec:.1f}**")
    st.divider()
    st.metric("Média Global", f"{med_global:.1f}")

# QUADRADO 4: Observações (Correção do Erro de Salvamento)
with m4:
    st.write("### Observações")
    with st.form("form_obs_v2"):
        # Mostra o que já está na planilha para aquela matéria
        obs_val = str(df_mat['Observações']) if pd.notna(df_mat['Observações']) else ""
        texto_obs = st.text_area("Notas:", value=obs_val, height=200)
        
        if st.form_submit_button("SALVAR"):
            # Localiza a linha exata (Aluno + Disciplina)
            idx_orig = df[(df['Aluno'] == aluno_atual) & (df['Disciplina'] == mat_escolhida)].index
            if not idx_orig.empty:
                # Grava explicitamente como string
                df.at[idx_orig[0], 'Observações'] = str(texto_obs)
                conn.update(data=df)
                st.success("Gravado!")
                st.balloons()

# --- NAVEGAÇÃO INFERIOR ---
st.divider()
c1, c2, c3 = st.columns([1,2,1])
with c1:
    if st.button("⬅️ Aluno Anterior"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx - 1) % len(alunos_lista)
        st.rerun()
with c2:
    # Seletor central por nome (funciona como o "dois cliques" do seu desenho)
    novo_aluno = st.selectbox("Ir para Aluno:", alunos_lista, index=st.session_state.aluno_idx)
    if novo_aluno != aluno_atual:
        st.session_state.aluno_idx = alunos_lista.index(novo_aluno)
        st.rerun()
with c3:
    if st.button("Próximo Aluno ➡️"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx + 1) % len(alunos_lista)
        st.rerun()
