import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração e Estilo
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
    .stButton>button { width: 100%; border: 1px solid #ddd; border-radius: 8px; text-align: left; }
    .stRadio > div { flex-direction: row; gap: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão e Dados
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")
df.columns = df.columns.str.strip()

if 'Observações' in df.columns:
    df['Observações'] = df['Observações'].astype(str).replace('nan', '')

# Estados de Sessão
if 'aluno_idx' not in st.session_state: st.session_state.aluno_idx = 0
if 'disciplina_ativa' not in st.session_state: st.session_state.disciplina_ativa = None
if 'reset_obs' not in st.session_state: st.session_state.reset_obs = 0

alunos_lista = df['Aluno'].unique().tolist()

# --- LÓGICA DE NAVEGAÇÃO (Movida para cima para atualizar o topo) ---
# Criamos o seletor aqui, mas ele só aparece visualmente no rodapé usando st.empty ou placeholders
# Para simplificar e garantir que funcione, vamos definir o aluno_nome AGORA
aluno_nome = alunos_lista[st.session_state.aluno_idx]
df_aluno = df[df['Aluno'] == aluno_nome].copy()

# --- TOPO: IDENTIFICAÇÃO (Agora sempre atualizado) ---
t1, t2 = st.columns([1, 4])
with t1:
    st.markdown("### Foto")
    st.image("https://via.placeholder.com/150", use_container_width=True)
with t2:
    st.subheader(f"Nome: {aluno_nome}")
    c1, c2 = st.columns(2)
    # Buscando direto do df_aluno que acabamos de filtrar
    c1.write(f"**Matrícula:** {df_aluno['Matrícula'].iloc[0]}")
    c2.write(f"**Série:** {df_aluno['Série'].iloc[0]}")

st.divider()

# --- OPÇÕES DE ORDENAÇÃO ---
ordem_bolinha = st.radio("Ordenar disciplinas por menor:", ["Nota", "Frequência"], horizontal=True)

# --- MIOLO: DISCIPLINAS | GRÁFICOS | GLOBAL | OBSERVAÇÕES ---
m1, m2, m3, m4 = st.columns([2, 3, 2, 2])

with m1:
    st.write("### Disciplinas")
    col_ref = 'Média Final' if ordem_bolinha == "Nota" else 'Freq. Final'
    df_lista = df_aluno.sort_values(by=col_ref, ascending=True)
    
    for disc in df_lista['Disciplina'].unique():
        if st.button(disc, key=f"btn_{disc}"):
            st.session_state.disciplina_ativa = disc
            st.session_state.reset_obs += 1
            st.rerun()

if st.session_state.disciplina_ativa is None:
    st.session_state.disciplina_ativa = df_aluno['Disciplina'].iloc[0]

df_mat = df_aluno[df_aluno['Disciplina'] == st.session_state.disciplina_ativa].iloc[0]

with m2:
    # Notas
    val_m_final = round(float(df_mat['Média Final']), 2)
    st.write(f"**Evolução: {st.session_state.disciplina_ativa} (Média Final: {val_m_final})**")
    fig_n = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI'], 
                   y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI']], markers=True)
    fig_n.update_yaxes(range=[0, 10.5])
    st.plotly_chart(fig_n, use_container_width=True)
    
    st.divider()
    
    # Frequência
    f_final_val = df_mat['Freq. Final']
    f_final_display = round(f_final_val * 100, 2) if f_final_val <= 1.0 else round(f_final_val, 2)
    st.write(f"**Frequência Mensal (Final: {f_final_display}%)**")
    
    meses_cols = ['Freq. Jan.', 'Freq. Fev.', 'Freq. Mar.', 'Freq. Abr.', 'Freq. Mai.', 'Freq. Jun.', 
                  'Freq. Jul.', 'Freq. Ago.', 'Freq. Set.', 'Freq. Out.', 'Freq. Nov.', 'Freq. Dez.']
    
    valores_f = []
    for m in meses_cols:
        val = df_mat[m]
        try:
            v = float(str(val).replace('%','').replace(',','.'))
            valores_f.append(round(v * 100, 2) if v <= 1.0 else round(v, 2))
        except: valores_f.append(0)
        
    fig_f = px.bar(x=[mes.split('.')[1].strip() for mes in meses_cols], y=valores_f)
    fig_f.update_yaxes(range=[0, 105], title="Porcentagem (%)")
    st.plotly_chart(fig_f, use_container_width=True)

with m3:
    st.write("### Global")
    m_comum = df_aluno[df_aluno['Núcleo'] == 'Comum']['Média Final'].mean()
    m_tec = df_aluno[df_aluno['Núcleo'] == 'Técnico']['Média Final'].mean()
    nota_mat_df = df_aluno[df_aluno['Disciplina'].str.contains('Matemática', case=False)]
    nota_mat = nota_mat_df['Média Final'].values[0] if not nota_mat_df.empty else 0
    
    st.write(f"Média Núcleo Comum: **{round(m_comum, 2)}**")
    st.write(f"Média Núcleo Técnico: **{round(m_tec, 2)}**")
    st.write(f"Média Matemática: **{round(float(nota_mat), 2)}**")
    st.divider()
    st.metric("Média Global", f"{round(df_aluno['Média Final'].mean(), 1)}")

with m4:
    st.write("### Observações")
    chave_base = f"{aluno_nome}_{st.session_state.disciplina_ativa}_{st.session_state.reset_obs}".replace(" ", "_")
    obs_banco = str(df_mat['Observações']) if pd.notna(df_mat['Observações']) else ""
    historico = [n.strip() for n in obs_banco.split(" | ") if n.strip() and n.lower() != "nan"]

    with st.form(key=f"form_{chave_base}"):
        entradas_atuais = []
        for i, texto in enumerate(historico):
            st.text_area(f"Nota {i+1}", value=texto, key=f"hist_{chave_base}_{i}", disabled=True)
            entradas_atuais.append(texto)
        
        nova_nota = st.text_area("Nova anotação...", value="", key=f"nova_{chave_base}")
        
        if st.form_submit_button("SALVAR"):
            if nova_nota.strip():
                entradas_atuais.append(nova_nota.strip())
                texto_final = " | ".join(entradas_atuais)
                idx = df[(df['Aluno'] == aluno_nome) & (df['Disciplina'] == st.session_state.disciplina_ativa)].index
                if not idx.empty:
                    df.at[idx[0], 'Observações'] = str(texto_final)
                    conn.update(data=df)
                    st.session_state.reset_obs += 1
                    st.success("Salvo!")
                    st.rerun()

# --- RODAPÉ: NAVEGAÇÃO ---
st.divider()
b1, b2, b3 = st.columns([1, 1, 1])
with b1:
    if st.button("⬅️ Anterior"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx - 1) % len(alunos_lista)
        st.session_state.disciplina_ativa = None
        st.session_state.reset_obs += 1
        st.rerun()
with b2:
    dict_chamada = {df[df['Aluno'] == a]['Nº Chamada'].iloc[0]: i for i, a in enumerate(alunos_lista)}
    num_atual = df_aluno['Nº Chamada'].iloc[0]
    
    # IMPORTANTE: O selectbox agora altera o estado e dá rerun IMEDIATO
    escolha_num = st.selectbox("Aluno Nº:", options=sorted(dict_chamada.keys()), 
                              index=sorted(dict_chamada.keys()).index(num_atual))
    
    if dict_chamada[escolha_num] != st.session_state.aluno_idx:
        st.session_state.aluno_idx = dict_chamada[escolha_num]
        st.session_state.disciplina_ativa = None
        st.session_state.reset_obs += 1
        st.rerun()
with b3:
    if st.button("Próximo ➡️"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx + 1) % len(alunos_lista)
        st.session_state.disciplina_ativa = None
        st.session_state.reset_obs += 1
        st.rerun()
