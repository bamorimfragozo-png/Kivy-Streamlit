import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# Configuração da Página e Estilo Visual (Bordas pretas arredondadas)
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
    .stButton>button { width: 100%; border: 1px solid #ddd; border-radius: 8px; text-align: left; padding: 10px; }
    .stRadio > div { flex-direction: row; gap: 20px; }
    </style>
    """, unsafe_allow_html=True)

# Conexão e Tratamento de Dados (Correção do TypeError)
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")
df.columns = df.columns.str.strip()

# Força a coluna de Observações a ser texto para evitar erros ao salvar
if 'Observações' in df.columns:
    df['Observações'] = df['Observações'].astype(str).replace('nan', '')

# Estados de Sessão para Navegação e Interatividade
if 'aluno_idx' not in st.session_state: st.session_state.aluno_idx = 0
if 'disciplina_ativa' not in st.session_state: st.session_state.disciplina_ativa = None

alunos_lista = df['Aluno'].unique().tolist()
aluno_nome = alunos_lista[st.session_state.aluno_idx]
df_aluno = df[df['Aluno'] == aluno_nome].copy()

# --- TOPO: IDENTIFICAÇÃO ---
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

# --- MIOLO: DISCIPLINAS | GRÁFICOS | GLOBAL | OBSERVAÇÕES ---
ordem_bolinha = st.radio("Ordenar disciplinas por menor:", ["Nota", "Frequência"], horizontal=True)

m1, m2, m3, m4 = st.columns([2, 3, 2, 2])

with m1:
    st.write("### Disciplinas")
    col_ref = 'Média Final' if ordem_bolinha == "Nota" else 'Freq. Final'
    df_lista = df_aluno.sort_values(by=col_ref, ascending=True)
    
    for disc in df_lista['Disciplina'].unique():
        val = df_lista[df_lista['Disciplina'] == disc][col_ref].values[0]
        # Se clicar no botão da disciplina, ela vira a ativa
        if st.button(f"{disc} — ({val})", key=f"btn_{disc}"):
            st.session_state.disciplina_ativa = disc
            st.rerun()

# Garante que uma disciplina esteja sempre selecionada
if st.session_state.disciplina_ativa is None:
    st.session_state.disciplina_ativa = df_aluno['Disciplina'].iloc[0]

df_mat = df_aluno[df_aluno['Disciplina'] == st.session_state.disciplina_ativa].iloc[0]

with m2:
    # Gráfico de Evolução Bimestral
    st.write(f"**Evolução: {st.session_state.disciplina_ativa}**")
    fig_n = px.line(x=['1º BI', '2º BI', '3º BI', '4º BI'], 
                   y=[df_mat['1º BI'], df_mat['2º BI'], df_mat['3º BI'], df_mat['4º BI']], markers=True)
    fig_n.update_yaxes(range=[0, 10.5])
    st.plotly_chart(fig_n, use_container_width=True)
    
    st.divider()
    
    # Gráfico de Frequência Mensal (%)
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
    st.plotly_chart(fig_f, use_container_width=True)

with m3:
    st.write("### Global")
    m_comum = df_aluno[df_aluno['Núcleo'] == 'Comum']['Média Final'].mean()
    m_tec = df_aluno[df_aluno['Núcleo'] == 'Técnico']['Média Final'].mean()
    nota_mat_df = df_aluno[df_aluno['Disciplina'].str.contains('Matemática', case=False)]
    nota_mat = nota_mat_df['Média Final'].values[0] if not nota_mat_df.empty else 0
    
    st.write(f"Média Núcleo Comum: **{m_comum:.2f}**")
    st.write(f"Média Núcleo Técnico: **{m_tec:.2f}**")
    st.write(f"Média Matemática: **{nota_mat:.2f}**")
    st.divider()
    st.metric("Média Global", f"{df_aluno['Média Final'].mean():.1f}")

with m4:
    st.write("### Observações")
    
    # 1. Carrega os dados da disciplina atual
    df_mat_obs = df_aluno[df_aluno['Disciplina'] == st.session_state.disciplina_ativa].iloc[0]
    obs_banco = str(df_mat_obs['Observações']) if pd.notna(df_mat_obs['Observações']) else ""
    
    # 2. Divide as notas e remove vazios/duplicados acidentais
    notas_historico = [n.strip() for n in obs_banco.split(" | ") if n.strip() and n != "nan"]
    if not notas_historico:
        notas_historico = [""]

    # 3. Criamos um contador no session_state para resetar as chaves dos inputs
    if 'form_reset' not in st.session_state:
        st.session_state.form_reset = 0

    with st.form("form_observacoes_final", clear_on_submit=True):
        caixas_atuais = []
        
        # Mostra as notas que já existem
        for i, texto in enumerate(notas_historico):
            # A key muda se st.session_state.form_reset mudar, limpando o campo
            conteudo = st.text_area(f"Nota {i+1}", value=texto, key=f"obs_{i}_{st.session_state.form_reset}")
            caixas_atuais.append(conteudo)
        
        # A caixa "discreta" para nova anotação: ela vem SEMPRE VAZIA (value="")
        nova_caixa = st.text_area("Adicionar nova anotação...", value="", key=f"nova_{st.session_state.form_reset}")
        caixas_atuais.append(nova_caixa)

        if st.form_submit_button("SALVAR ALTERAÇÕES"):
            # 4. Processa o texto: remove espaços e entradas vazias
            # O set() seguido de sorted(..., key=caixas_atuais.index) evita duplicados mantendo a ordem
            lista_limpa = []
            for item in caixas_atuais:
                limpo = item.strip()
                if limpo and limpo not in lista_limpa:
                    lista_limpa.append(limpo)
            
            texto_final = " | ".join(lista_limpa)
            
            # 5. Grava na Planilha
            filtro = (df['Aluno'] == aluno_nome) & (df['Disciplina'] == st.session_state.disciplina_ativa)
            idx_linha = df.index[filtro].tolist()
            
            if idx_linha:
                df.at[idx_linha[0], 'Observações'] = str(texto_final)
                conn.update(data=df)
                
                # 6. MUITO IMPORTANTE: Incrementa o reset para limpar os campos na próxima carga
                st.session_state.form_reset += 1
                st.success("Salvo com sucesso!")
                st.rerun()

# --- RODAPÉ: NAVEGAÇÃO ---
st.divider()
b1, b2, b3 = st.columns([1, 1, 1])
with b1:
    if st.button("⬅️ Anterior"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx - 1) % len(alunos_lista)
        st.rerun()
with b2:
    # Seletor Numérico conforme desenho (Nº Chamada)
    dict_chamada = {df[df['Aluno'] == a]['Nº Chamada'].iloc[0]: i for i, a in enumerate(alunos_lista)}
    num_atual = df_aluno['Nº Chamada'].iloc[0]
    
    escolha_num = st.selectbox(
        "Ir para Aluno (Nº Chamada):", 
        options=sorted(dict_chamada.keys()),
        index=sorted(dict_chamada.keys()).index(num_atual)
    )
    if dict_chamada[escolha_num] != st.session_state.aluno_idx:
        st.session_state.aluno_idx = dict_chamada[escolha_num]
        st.rerun()
with b3:
    if st.button("Próximo ➡️"):
        st.session_state.aluno_idx = (st.session_state.aluno_idx + 1) % len(alunos_lista)
        st.rerun()
