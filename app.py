import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração e Título
st.set_page_config(page_title="Dashboard Acadêmico", layout="wide")

# 2. Conexão (Editor para poder salvar)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    return conn.read(ttl="0")

df = get_data()
df.columns = df.columns.str.strip()

# --- CABEÇALHO ---
st.title("🛡️ Sistema de Gestão Acadêmica")
col_foto, col_info = st.columns([1, 4])

with col_foto:
    st.image("https://via.placeholder.com/150")

with col_info:
    aluno_sel = st.selectbox("Selecione o Aluno:", df['Aluno'].unique())
    df_aluno = df[df['Aluno'] == aluno_sel].copy()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Matrícula", df_aluno['Matrícula'].iloc[0])
    c2.metric("Série", df_aluno['Série'].iloc[0])
    c3.metric("Média Global", f"{df_aluno['Média Final'].mean():.1f}")

st.divider()

# --- CORPO ---
col_disc, col_graficos, col_obs = st.columns([1.5, 3, 1.5])

with col_disc:
    st.subheader("📚 Disciplinas")
    ordem = st.radio("Ordenar menor valor por:", ["Nota", "Frequência"])
    col_ref = 'Média Final' if ordem == "Nota" else 'Frequência'
    
    # Tabela Interativa de Disciplinas
    df_lista = df_aluno[['Disciplina', col_ref]].sort_values(by=col_ref)
    
    # Mostra uma tabela onde o usuário pode clicar
    selecionado = st.selectbox("Clique para selecionar a matéria:", df_lista['Disciplina'])
    df_materia = df_aluno[df_aluno['Disciplina'] == selecionado].iloc[0]

with col_graficos:
    st.subheader(f"Análise: {selecionado}")
    
    # Gráfico 1: Evolução de Notas
    bimestres = ['1º BI', '2º BI', '3º BI', '4º BI']
    notas = [df_materia[b] for b in bimestres]
    fig_n = px.line(x=bimestres, y=notas, markers=True, title="Notas por Bimestre")
    fig_n.update_yaxes(range=[0, 10])
    st.plotly_chart(fig_n, use_container_width=True)
    
    # Gráfico 2: Frequência
    # Usando o valor de frequência da planilha para um gráfico simples
    fig_f = px.bar(x=["Frequência Atual", "Meta"], y=[df_materia['Frequência'], 100], 
                   color=["Real", "Meta"], title="Frequência vs Meta (%)")
    st.plotly_chart(fig_f, use_container_width=True)

with col_obs:
    st.subheader("📝 Observações +")
    # Puxa o que já estiver na planilha (mesmo que seja vazio)
    texto_atual = str(df_materia['Observações']) if pd.notna(df_materia['Observações']) else ""
    nova_obs = st.text_area("Registrar nova nota:", value=texto_atual, height=300)
    
    if st.button("💾 Salvar na Planilha"):
        # Lógica de atualização
        # Nota: Para o .update() funcionar, você precisa passar o DataFrame completo 
        # ou usar a função de atualização da biblioteca.
        df.loc[(df['Aluno'] == aluno_sel) & (df['Disciplina'] == selecionado), 'Observações'] = nova_obs
        conn.update(worksheet="Página1", data=df)
        st.success("Gravado com sucesso!")
        st.balloons()

# --- RODAPÉ GLOBAL ---
st.divider()
st.subheader("📊 Médias por Núcleo")
g1, g2, g3 = st.columns(3)
# Filtro por categoria se existir na planilha
if 'Categoria' in df_aluno.columns:
    tec = df_aluno[df_aluno['Categoria'] == 'Técnico']['Média Final'].mean()
    com = df_aluno[df_aluno['Categoria'] == 'Comum']['Média Final'].mean()
    mat = df_aluno[df_aluno['Disciplina'] == 'Matemática']['Média Final'].mean()
    g1.metric("Núcleo Técnico", f"{tec:.1f}")
    g2.metric("Núcleo Comum", f"{com:.1f}")
    g3.metric("Matemática", f"{mat:.1f}")
