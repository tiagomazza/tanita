import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração visual da página
st.set_page_config(page_title="Análise Tanita BC-601", layout="wide", page_icon="⚖️")

st.title("📊 Monitor de Composição Corporal (BC-601)")
st.markdown("---")

def processar_dados_tanita(conteudo_arquivo):
    registros = []
    
    # Mapeamento das siglas do dispositivo para nomes amigáveis
    mapeamento = {
        'DT': 'Data', 'Ti': 'Hora', 'AG': 'Idade', 'Wk': 'Peso_kg',
        'MI': 'IMC', 'FW': 'Gordura_Total_pct', 'mW': 'Massa_Muscular_kg',
        'bW': 'Massa_Ossea_kg', 'IF': 'Gordura_Visceral', 'rD': 'TMB_kcal',
        'rA': 'Idade_Metabolica', 'ww': 'Agua_Corporal_pct'
    }

    for linha in conteudo_arquivo:
        # Ignora linhas vazias ou de formatação (ex: | ------ |)
        if not linha.strip() or '---' in linha:
            continue
            
        # Divide a linha por '|' e limpa os espaços
        partes = [p.strip() for p in linha.split('|') if p.strip()]
        
        # Cria um dicionário para a linha atual buscando as chaves do mapeamento
        dados_linha = {}
        for sigla in mapeamento.keys():
            if sigla in partes:
                indice = partes.index(sigla)
                if indice + 1 < len(partes):
                    dados_linha[mapeamento[sigla]] = partes[indice + 1]
        
        if dados_linha:
            registros.append(dados_linha)

    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)

    # Conversão de Data e Hora com tratamento de erro (coerce transforma erro em NaT)
    if 'Data' in df.columns and 'Hora' in df.columns:
        df['Timestamp'] = pd.to_datetime(
            df['Data'] + ' ' + df['Hora'], 
            dayfirst=True, 
            errors='coerce'
        )
        # Remove registros onde a data/hora resultou em erro
        df = df.dropna(subset=['Timestamp'])

    # Conversão de colunas numéricas
    colunas_num = [c for c in df.columns if c not in ['Data', 'Hora', 'Timestamp']]
    for col in colunas_num:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('Timestamp')

# Interface Lateral para Upload
with st.sidebar:
    st.header("Configurações")
    arquivo = st.file_uploader("Selecione o arquivo DATA1.CSV", type=["csv", "txt"])

if arquivo:
    # Lê o arquivo e processa
    linhas = arquivo.getvalue().decode("utf-8").splitlines()
    df_processado = processar_dados_tanita(linhas)

    if not df_processado.empty:
        # --- BLOCO DE MÉTRICAS (Última Medição) ---
        ultimo = df_processado.iloc[-1]
        st.subheader(f"📅 Última Medição: {ultimo['Timestamp'].strftime('%d/%m/%Y %H:%M')}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Peso", f"{ultimo['Peso_kg']} kg")
        m2.metric("Gordura", f"{ultimo['Gordura_Total_pct']}%")
        m3.metric("Massa Muscular", f"{ultimo['Massa_Muscular_kg']} kg")
        m4.metric("Idade Metabólica", f"{int(ultimo['Idade_Metabolica'])} anos")

        st.markdown("---")

        # --- BLOCO DE GRÁFICOS ---
        tab1, tab2 = st.tabs(["📉 Evolução de Peso e Gordura", "💪 Massa Muscular e Água"])
        
        with tab1:
            fig_peso = px.line(df_processado, x='Timestamp', y=['Peso_kg', 'Gordura_Total_pct'], 
                              title="Tendência de Peso e % de Gordura",
                              markers=True, labels={"value": "Valor", "Timestamp": "Data"})
            st.plotly_chart(fig_peso, use_container_width=True)

        with tab2:
            fig_musculo = px.area(df_processado, x='Timestamp', y='Massa_Muscular_kg', 
                                title="Evolução da Massa Muscular",
                                color_discrete_sequence=['#2ca02c'])
            st.plotly_chart(fig_musculo, use_container_width=True)

        # --- TABELA DE DADOS ---
        with st.expander("Visualizar Histórico Completo"):
            st.dataframe(df_processado.drop(columns=['Timestamp']).style.highlight_max(axis=0))
    else:
        st.error("O arquivo carregado não contém dados compatíveis com o BC-601.")
else:
    st.info("Por favor, carregue o arquivo DATA1.CSV para visualizar sua análise.")
