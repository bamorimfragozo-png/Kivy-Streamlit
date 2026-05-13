import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# Configuração e Estilo
st.set_page_config(page_title="Dashboard Escolar", layout="wide")

st.markdown("""
    <style>
    /* Estilo para todos os quadrados do dashboard */
    [data-testid="stColumn"] {
        border: 2px solid black !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# Conexão
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")
df.columns = df.columns.str.strip()

# Forçar a coluna de Observações a ser texto para evitar o TypeError
if 'Observações' in df.columns:
    df['Observações'] = df['Observações'].astype(str).replace('nan', '')

# Navegação de Alunos
if 'aluno_idx' not in st.session_state: st.session_state.aluno_idx = 0
alunos_lista = df['Aluno'].unique().tolist()
aluno_atual = alunos_lista[st.session_state.aluno_idx]
df_aluno = df[df['Aluno'] == aluno_atual].copy()

# --- LAYOUT SUPERIOR ---
t1, t2 = st.columns([1, 4])
with t1:
    st.markdown("### Foto")
    st.image("https://via.placeholder.com/150")
with t2:
    st.subheader(f"Aluno: {aluno_atual}")
    st.write(f"Matrícula: {df_aluno['Matrícula'].iloc[0]} | Série: {df_aluno['Série'].iloc[0]}")

# --- MIOLO DO DASHBOARD ---
# Coluna 1: Lista de Disciplinas (Interativa)
m1, m2, m3, m4 = st.columns([2.5, 3, 2, 2])

with m1:
    st.write("### Disciplinas")
    ordem = st.radio("Ordenar por:", ["Nota", "Frequência"], horizontal=True)
    col_sort = 'Média Final' if ordem == "Nota" else 'Freq. Final'
    
    # Tabela interativa para selecionar a disciplina
    df_mostra = df_aluno[['Disciplina', col_sort]].sort_values(by=col_sort)
    selecao = st.dataframe(
        df_mostra,
        on_select="rerun",
        selection_mode="single_row",
        hide_index=True,
        use_container_width=True
    )
    
    # Define qual disciplina mostrar nos gráficos
    if len(selecao.selection.rows) > 0:
        idx_sel = selecao.selection.rows[0]
        mat_escolhida = df_mostra.iloc[idx_sel]['Disciplina']
    else:
        mat_escolhida = df_aluno['Disciplina'].iloc[0]

# Coluna 2: Gráficos (Agora em quadrados separados internamente)
with m2:
    df_mat = df_aluno[df_aluno['Disciplina'] == mat_escolhida].iloc[0]
    
    # Sub-quadrado para Evolução de Notas
    st.markdown(f"**Evolução: {mat_escolhida}**")
    fig_notas = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI'], 
                        y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI']],
                        markers=True)
    fig_notas.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=200)
    st.plotly_chart(fig_notas, use_container_width=True)
    
    st.divider() # Linha para separar visualmente os gráficos
    
    # Sub-quadrado para Frequência Mensal (Em Porcentagem)
    st.markdown("**Frequência Mensal (%)**")
    meses = ['Freq. Jan.', 'Freq. Fev.', 'Freq. Mar.', 'Freq. Abr.', 'Freq. Mai.', 'Freq. Jun.', 
             'Freq. Jul.', 'Freq. Ago.', 'Freq. Set.', 'Freq. Out.', 'Freq. Nov.', 'Freq. Dez.']
    # Converte decimal (ex: 0.85) para porcentagem (85)
    valores_pento = [float(str(df_mat[m]).replace('%','').replace(',','.')) * 100 if df_mat[m] < 1 else df_mat[m] for m in meses]
    
    fig_freq = px.bar(x=[m.split('.')[1] for m in meses], y=valores_pento)
    fig_freq.update_yaxes(title="%", range=[0, 100])
    fig_freq.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=200)
    st.plotly_chart(fig_freq, use_container_width=True)

with m3:
    st.write("### Global")
    med_global = df_aluno['Média Final'].mean()
    # Usa o nome correto da coluna 'Núcleo' conforme seu print
    med_comum = df_aluno[df_aluno['Núcleo'] == 'Comum']['Média Final'].mean()
    med_tec = df_aluno[df_aluno['Núcleo'] == 'Técnico']['Média Final'].mean()
    
    st.write(f"Média Núcleo Comum: **{med_comum:.1f}**")
    st.write(f"Média Núcleo Técnico: **{med_tec:.1f}**")
    st.divider()
    st.metric("Média Global", f"{med_global:.1f}")

with m4:
    st.write("### Observações")
    with st.form("form_obs"):
        obs_texto = st.text_area("Notas/Ocorrências:", value=str(df_mat['Observações']) if pd.notna(df_mat['Observações']) else "")
        if st.form_submit_button("SALVAR"):
            # Acha a linha e salva como STRING para evitar o TypeError
            idx_planilha = df[(df['Aluno'] == aluno_atual) & (df['Disciplina'] == mat_escolhida)].index
            df.at[idx_planilha[0], 'Observações'] = str(obs_texto)
            conn.update(data=df)
            st.success("Salvo com sucesso!")

# Navegação Inferior
st.divider()
c_nav1, c_nav2, c_nav3 = st.columns([1,1,1])
with c_nav1:
    if st.button("⬅️ Aluno Anterior"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx - 1) % len(alunos_lista)
        st.rerun()
with c_nav3:
    if st.button("Próximo Aluno ➡️"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx + 1) % len(alunos_lista)
        st.rerun()
