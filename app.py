import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração e Estilo Visual
st.set_page_config(page_title="Dashboard Escolar v2", layout="wide")

st.markdown("""
    <style>
    [data-testid="stColumn"] {
        border: 2px solid black !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
        margin-bottom: 15px;
    }
    .stRadio > div { flex-direction: row; gap: 20px; margin-bottom: -10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão com os dados (Nova Planilha)
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")
df.columns = df.columns.str.strip()

# Estados de sessão para navegação
if 'aluno_idx' not in st.session_state: st.session_state.aluno_idx = 0
if 'num_notas' not in st.session_state: st.session_state.num_notas = 1

alunos_lista = df['Aluno'].unique().tolist()
aluno_atual = alunos_lista[st.session_state.aluno_idx]
df_aluno = df[df['Aluno'] == aluno_atual].copy()

# --- TOPO: IDENTIFICAÇÃO ---
t1, t2 = st.columns([1, 4])
with t1:
    st.markdown("### Foto")
    st.image("https://via.placeholder.com/150", caption=f"Foto de {aluno_atual}")
with t2:
    st.subheader(f"Nome: {aluno_atual}")
    c1, c2, c3 = st.columns(3)
    c1.write(f"**Matrícula:** {df_aluno['Matrícula'].iloc[0]}")
    c2.write(f"**Série:** {df_aluno['Série'].iloc[0]}")
    c3.write(f"**Nº Chamada:** {df_aluno['Nº Chamada'].iloc[0]}")

# --- OPÇÕES FORA DOS QUADRADOS ---
ordem = st.radio("Ordenar disciplinas por menor:", ["Nota", "Frequência"])

# --- MIOLO DO DASHBOARD ---
m1, m2, m3, m4 = st.columns([2, 3, 2, 2])

with m1:
    st.write("### Disciplinas")
    col_v = 'Média Final' if ordem == "Nota" else 'Freq. Final'
    df_tab = df_aluno.sort_values(by=col_v, ascending=True)
    st.table(df_tab[['Disciplina', col_v]])

with m2:
    # Seletor de matéria dentro do gráfico
    materia_sel = st.selectbox("Escolha a Matéria:", df_aluno['Disciplina'].unique())
    df_mat = df_aluno[df_aluno['Disciplina'] == materia_sel].iloc[0]
    
    # Gráfico de Notas (Bimestrais)
    fig_notas = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI'], 
                        y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI']],
                        markers=True, title=f"Notas: {materia_sel}")
    fig_notas.update_yaxes(range=[0, 10.5])
    st.plotly_chart(fig_notas, use_container_width=True)
    
    # Gráfico de Frequência Mensal (Usando suas novas colunas)
    meses = ['Freq. Jan.', 'Freq. Fev.', 'Freq. Mar.', 'Freq. Abr.', 'Freq. Mai.', 'Freq. Jun.', 
             'Freq. Jul.', 'Freq. Ago.', 'Freq. Set.', 'Freq. Out.', 'Freq. Nov.', 'Freq. Dez.']
    valores_freq = [df_mat[m] for m in meses]
    
    fig_freq = px.bar(x=[m.replace('Freq. ', '') for m in meses], y=valores_freq, 
                      title="Frequência Mensal (%)", range_y=[0, 1.1]) # 1.1 pois está em decimal/percentual
    st.plotly_chart(fig_freq, use_container_width=True)

with m3:
    st.write("### Global")
    # Cálculos automáticos baseados na coluna 'Núcleo'
    med_global = df_aluno['Média Final'].mean()
    med_comum = df_aluno[df_aluno['Núcleo'] == 'Comum']['Média Final'].mean()
    med_tec = df_aluno[df_aluno['Núcleo'] == 'Técnico']['Média Final'].mean()
    
    # Busca nota de matemática
    nota_mat = df_aluno[df_aluno['Disciplina'].str.contains('Matemática', case=False)]['Média Final'].values
    val_mat = nota_mat[0] if len(nota_mat) > 0 else 0
    
    st.write(f"**Média núcleo comum:** {med_comum:.2f}")
    st.write(f"**Média núcleo técnico:** {med_tec:.2f}")
    st.write(f"**Média matemática:** {val_mat:.2f}")
    st.divider()
    st.metric("Média Global", f"{med_global:.1f}")

with m4:
    st.write("### Observações")
    if st.button("➕", help="Adicionar linha"):
        st.session_state.num_notas += 1
    
    with st.form("save_obs"):
        obs_atual = str(df_mat['Observações']) if pd.notna(df_mat['Observações']) else ""
        notas_inputs = []
        for i in range(st.session_state.num_notas):
            val = obs_atual if i == 0 else ""
            notas_inputs.append(st.text_area(f"Nota {i+1}", value=val, key=f"obs_{i}"))
        
        if st.form_submit_button("SALVAR NA PLANILHA"):
            texto_unido = " | ".join([n for n in notas_inputs if n.strip()])
            # Acha a linha exata na planilha original
            idx = df[(df['Aluno'] == aluno_atual) & (df['Disciplina'] == materia_sel)].index
            if not idx.empty:
                df.at[idx[0], 'Observações'] = texto_unido
                conn.update(data=df)
                st.success("Salvo!")

# --- RODAPÉ: NAVEGAÇÃO ---
st.divider()
b1, b2, b3 = st.columns([1, 1, 1])
with b1:
    if st.button("⬅️ Anterior"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx - 1) % len(alunos_lista)
        st.rerun()
with b2:
    # Seletor por número da chamada (Ex: clicou no 6, vai para a Bianca)
    n_escolha = st.selectbox("Número do Aluno:", options=range(len(alunos_lista)),
                            index=st.session_state.aluno_idx,
                            format_func=lambda x: f"Nº {df[df['Aluno'] == alunos_lista[x]]['Nº Chamada'].iloc[0]}")
    if n_escolha != st.session_state.aluno_idx:
        st.session_state.aluno_idx = n_escolha
        st.rerun()
with b3:
    if st.button("Próximo ➡️"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx + 1) % len(alunos_lista)
        st.rerun()
