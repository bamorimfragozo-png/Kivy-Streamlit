import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração de Estilo (Fiel ao desenho do Paint)
st.set_page_config(page_title="Gestão Acadêmica", layout="wide")

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
    .stTextArea textarea { border: 1px solid #ccc !important; height: 80px; }
    .stButton > button { border: 1px solid black !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão e Dados
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")
df.columns = df.columns.str.strip()

# Garantir que a coluna de Observações aceite texto (evita o TypeError)
if 'Observações' in df.columns:
    df['Observações'] = df['Observações'].astype(str).replace('nan', '')

# 3. Estados de Sessão
if 'aluno_idx' not in st.session_state: st.session_state.aluno_idx = 0
if 'disciplina_ativa' not in st.session_state: st.session_state.disciplina_ativa = None

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

st.divider()

# --- MIOLO: DISCIPLINAS | GRÁFICOS | GLOBAL | OBSERVAÇÕES ---
# Opções de ordenação fora dos quadros (bolinhas)
col_radio_ordem = st.radio("Ordenar disciplinas por menor:", ["Nota", "Frequência"], horizontal=True)

m1, m2, m3, m4 = st.columns([2, 3, 2, 2])

with m1:
    st.write("### Disciplinas")
    col_ref = 'Média Final' if col_radio_ordem == "Nota" else 'Freq. Final'
    df_lista = df_aluno.sort_values(by=col_ref, ascending=True)
    
    # Seleção por clique (Radio estilizado como lista)
    disciplina_sel = st.radio(
        "Selecione a matéria para mudar o gráfico:",
        df_lista['Disciplina'].unique(),
        label_visibility="collapsed"
    )
    st.session_state.disciplina_ativa = disciplina_sel
    df_mat = df_aluno[df_aluno['Disciplina'] == disciplina_sel].iloc[0]

with m2:
    # QUADRO DE NOTAS
    st.write(f"**Evolução: {disciplina_sel}**")
    fig_n = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI'], 
                   y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI']], markers=True)
    fig_n.update_yaxes(range=[0, 10.5])
    fig_n.update_layout(height=180, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig_n, use_container_width=True)
    
    st.divider()
    
    # QUADRO DE FREQUÊNCIA MENSAL (%)
    st.write("**Frequência Mensal (%)**")
    meses_cols = ['Freq. Jan.', 'Freq. Fev.', 'Freq. Mar.', 'Freq. Abr.', 'Freq. Mai.', 'Freq. Jun.', 
                  'Freq. Jul.', 'Freq. Ago.', 'Freq. Set.', 'Freq. Out.', 'Freq. Nov.', 'Freq. Dez.']
    
    valores_f = []
    for m in meses_cols:
        val = df_mat[m]
        try:
            v = float(str(val).replace('%','').replace(',','.'))
            valores_f.append(v * 100 if v <= 1.0 else v)
        except: valores_f.append(0)
        
    fig_f = px.bar(x=[m.split('.')[1].strip() for m in meses_cols], y=valores_f)
    fig_f.update_yaxes(range=[0, 105])
    fig_f.update_layout(height=180, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig_f, use_container_width=True)

with m3:
    st.write("### Global")
    # Cálculos dinâmicos por aluno
    m_comum = df_aluno[df_aluno['Núcleo'] == 'Comum']['Média Final'].mean()
    m_tec = df_aluno[df_aluno['Núcleo'] == 'Técnico']['Média Final'].mean()
    # Busca matemática especificamente
    nota_mat_row = df_aluno[df_aluno['Disciplina'].str.contains('Matemática', case=False)]
    nota_mat = nota_mat_row['Média Final'].values[0] if not nota_mat_row.empty else 0
    
    st.write(f"Média Núcleo Comum: **{m_comum:.2f}**")
    st.write(f"Média Núcleo Técnico: **{m_tec:.2f}**")
    st.write(f"Média Matemática: **{nota_mat:.2f}**")
    st.divider()
    st.metric("Média Global", f"{df_aluno['Média Final'].mean():.1f}")

with m4:
    st.write("### Observações")
    # Lógica de "brotar" nova caixa: se a última estiver preenchida, mostra outra
    obs_banco = str(df_mat['Observações']) if pd.notna(df_mat['Observações']) else ""
    lista_obs = obs_banco.split(" | ") if obs_banco else [""]
    
    with st.form("salvar_obs_form"):
        novas_entradas = []
        for i, texto in enumerate(lista_obs):
            ent = st.text_area(f"Nota {i+1}", value=texto, key=f"obs_{i}")
            novas_entradas.append(ent)
        
        # A "caixa discreta" adicional que surge se a última tiver texto
        if novas_entradas[-1].strip() != "":
            extra = st.text_area("Nova Observação +", key="extra_obs")
            novas_entradas.append(extra)
            
        if st.form_submit_button("SALVAR ALTERAÇÕES"):
            texto_final = " | ".join([n.strip() for n in novas_entradas if n.strip()])
            idx = df[(df['Aluno'] == aluno_atual) & (df['Disciplina'] == disciplina_sel)].index
            df.at[idx[0], 'Observações'] = str(texto_final)
            conn.update(data=df)
            st.success("Salvo!")
            st.rerun()

# --- RODAPÉ: NAVEGAÇÃO ---
st.divider()
b1, b2, b3 = st.columns([1, 1, 1])
with b1:
    if st.button("⬅️ Anterior"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx - 1) % len(alunos_lista)
        st.rerun()
with b2:
    # Seletor numérico por Número da Chamada (conforme imagem)
    num_chamada_atual = df_aluno['Nº Chamada'].iloc[0]
    opcoes_num = {df[df['Aluno'] == a]['Nº Chamada'].iloc[0]: i for i, a in enumerate(alunos_lista)}
    
    escolha_num = st.selectbox(
        "Ir para Aluno (Nº Chamada):", 
        options=sorted(opcoes_num.keys()),
        index=sorted(opcoes_num.keys()).index(num_chamada_atual)
    )
    if opcoes_num[escolha_num] != st.session_state.aluno_idx:
        st.session_state.aluno_idx = opcoes_num[escolha_num]
        st.rerun()
with b3:
    if st.button("Próximo ➡️"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx + 1) % len(alunos_lista)
        st.rerun()
