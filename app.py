import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard Acadêmico", layout="wide")

# CSS PARA FORÇAR O VISUAL DO PAINT (BORDAS PRETAS ARREDONDADAS)
st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > div:has(div.stColumn) > div.stColumn {
        border: 2px solid black;
        border-radius: 15px;
        padding: 15px;
        background-color: #ffffff;
        margin-bottom: 10px;
    }
    .stButton > button {
        width: 100%;
        border: 1px solid black;
    }
    </style>
    """, unsafe_allow_html=True)

# CONEXÃO COM A PLANILHA
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")
df.columns = df.columns.str.strip()

# CONTROLE DE ESTADO (NAVEGAÇÃO E OBSERVAÇÕES)
if 'idx_aluno' not in st.session_state: st.session_state.idx_aluno = 0
if 'notas_dinamicas' not in st.session_state: st.session_state.notas_dinamicas = [""]

# DADOS DO ALUNO ATUAL
lista_alunos = df['Aluno'].unique().tolist()
aluno_atual = lista_alunos[st.session_state.idx_aluno]
df_aluno = df[df['Aluno'] == aluno_atual].copy()

# --- TOPO: FOTO | NOME / MATRÍCULA ---
col_foto, col_info = st.columns([1, 4])

with col_foto:
    st.markdown("### Foto")
    st.image("https://via.placeholder.com/150", caption="Foto do Aluno")

with col_info:
    st.write(f"**Nome:** {aluno_atual}")
    st.write(f"**Matrícula:** {df_aluno['Matrícula'].iloc[0]}")
    st.write(f"**Série:** {df_aluno['Série'].iloc[0]}")

st.divider()

# --- CORPO: DISCIPLINAS | GRÁFICOS | GLOBAL | OBSERVAÇÕES ---
c_disc, c_graf, c_glob, c_obs = st.columns([1.5, 3, 1.5, 1.5])

with c_disc:
    st.subheader("Disciplinas")
    criterio = st.radio("Ordenar por menor:", ["Nota", "Frequência"])
    col_ref = 'Média Final' if criterio == "Nota" else 'Frequência'
    
    # Ordena conforme solicitado (Menor no topo)
    df_ord = df_aluno.sort_values(by=col_ref, ascending=True)
    
    # Simulação da tabela clicável usando botões (Retângulos)
    for d in df_ord['Disciplina'].unique():
        if st.button(f"{d} ({df_ord[df_ord['Disciplina']==d][col_ref].values[0]})"):
            st.session_state.materia_ativa = d

if 'materia_ativa' not in st.session_state:
    st.session_state.materia_ativa = df_aluno['Disciplina'].iloc[0]

df_mat = df_aluno[df_aluno['Disciplina'] == st.session_state.materia_ativa].iloc[0]

with c_graf:
    st.subheader(f"Dashboard: {st.session_state.materia_ativa}")
    # Gráfico 1: Evolução Bimestral
    fig1 = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI', 'Final'], 
                  y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI'], df_mat['Final']],
                  markers=True, title="Evolução Bimestral")
    st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico 2: Frequência Mensal (Simulado conforme imagem)
    fig2 = px.bar(x=['Jan', 'Fev', 'Mar', 'Abr'], y=[80, 95, 70, 90], title="Dividido por meses")
    st.plotly_chart(fig2, use_container_width=True)

with c_glob:
    st.subheader("Global")
    st.write(f"**Média Núcleo Comum:** {df_aluno[df_aluno['Categoria']=='Comum']['Média Final'].mean():.1f}")
    st.write(f"**Média Núcleo Técnico:** {df_aluno[df_aluno['Categoria']=='Técnico']['Média Final'].mean():.1f}")
    st.write(f"**Média Matemática:** {df_aluno[df_aluno['Disciplina']=='Matemática']['Média Final'].values[0]}")
    st.divider()
    st.metric("Média Global", f"{df_aluno['Média Final'].mean():.1f}")

with c_obs:
    st.subheader("Observações +")
    # O BOTÃO "+" QUE ACRESCENTA NOVAS CAIXAS
    if st.button("➕"):
        st.session_state.notas_dinamicas.append("")
    
    with st.form("save_obs"):
        for i, val in enumerate(st.session_state.notas_dinamicas):
            st.session_state.notas_dinamicas[i] = st.text_area(f"Nota {i+1}", value=val, key=f"text_{i}")
        
        if st.form_submit_button("Salvar na Planilha"):
            obs_texto = " | ".join(st.session_state.notas_dinamicas)
            df.loc[(df['Aluno'] == aluno_atual) & (df['Disciplina'] == st.session_state.materia_ativa), 'Observações'] = obs_texto
            conn.update(data=df)
            st.success("Salvo!")

# --- RODAPÉ: SETAS DE NAVEGAÇÃO ---
st.divider()
b_voltar, b_espaco, b_avancar = st.columns([1, 4, 1])

with b_voltar:
    if st.button("⬅️ Anterior"):
        st.session_state.idx_aluno = (st.session_state.idx_aluno - 1) % len(lista_alunos)
        st.rerun()

with b_avancar:
    if st.button("Próximo ➡️"):
        st.session_state.idx_aluno = (st.session_state.idx_aluno + 1) % len(lista_alunos)
        st.rerun()
