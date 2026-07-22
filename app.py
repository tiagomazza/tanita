import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página para um aspeto profissional
st.set_page_config(page_title="Tanita BC-601 Dashboard", layout="wide", page_icon="⚖️")

st.title("📊 Analisador de Composição Corporal (BC-601)")
st.markdown("---")

def processar_arquivo_tanita(file_bytes):
    # Tenta decodificação UTF-8 e usa Latin-1 como alternativa para ficheiros de cartões SD
    try:
        conteudo = file_bytes.decode('utf-8', errors='ignore')
    except:
        conteudo = file_bytes.decode('latin-1', errors='ignore')
    
    linhas = conteudo.splitlines()
    registros = []
    
    # Mapeamento das siglas do dispositivo BC-601 conforme as fontes
    mapeamento = {
        'DT': 'Data', 'Ti': 'Hora', 'Wk': 'Peso_kg', 'MI': 'IMC', 
        'FW': 'Gordura_Total_pct', 'mW': 'Massa_Muscular_kg', 
        'bW': 'Massa_Ossea_kg', 'IF': 'Gordura_Visceral', 
        'rD': 'TMB_kcal', 'rA': 'Idade_Metabolica', 'ww': 'Agua_Corporal_pct'
    }

    for linha in linhas:
        # Só processa linhas que contêm a identificação do modelo BC-601
        if "BC-601" not in linha:
            continue
            
        # Limpeza: remove aspas, chavetas e espaços (essencial para ler "11/07/2023")
        linha_limpa = linha.replace('"', '').replace('{', '').replace('}', '').strip()
        
        # Divide a linha por vírgula ou pipe para extrair os segmentos
        partes = [p.strip() for p in linha_limpa.replace('|', ',').split(',') if p.strip()]
        
        dados_linha = {}
        for sigla, nome_coluna in mapeamento.items():
            if sigla in partes:
                idx = partes.index(sigla)
                if idx + 1 < len(partes):
                    dados_linha[nome_coluna] = partes[idx + 1]
        
        if dados_linha:
            registros.append(dados_linha)

    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)

    # Conversão de Timestamp (Data + Hora)
    if 'Data' in df.columns and 'Hora' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Timestamp'])

    # Conversão de todas as métricas para formato numérico para cálculos e gráficos
    colunas_numericas = [c for c in df.columns if c not in ['Data', 'Hora', 'Timestamp']]
    for col in colunas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('Timestamp')

# Interface Lateral
arquivo = st.sidebar.file_uploader("Selecione o ficheiro DATA1.CSV", type=["csv", "txt"])

if arquivo:
    df = processar_arquivo_tanita(arquivo.getvalue())

    if not df.empty:
        # CORREÇÃO DEFINITIVA: Uso de .iloc para a primeira linha e .iloc[-1] para a última
        primeira = df.iloc
        ultima = df.iloc[-1]
        
        # Agora o acesso a ['Data'] funciona corretamente como string
        st.subheader(f"📅 Período de Análise: {primeira['Data']} até {ultima['Data']}")
        
        # KPIs principais
        c1, c2, c3, c4 = st.columns(4)
        
        variacao_peso = ultima['Peso_kg'] - primeira['Peso_kg']
        variacao_musculo = ultima['Massa_Muscular_kg'] - primeira['Massa_Muscular_kg']
        
        c1.metric("Peso Atual", f"{ultima['Peso_kg']} kg", f"{variacao_peso:.1f} kg")
        c2.metric("Massa Muscular", f"{ultima['Massa_Muscular_kg']} kg", f"{variacao_musculo:.1f} kg")
        c3.metric("Gordura Corporal", f"{ultima['Gordura_Total_pct']}%")
        c4.metric("Idade Metabólica", f"{int(ultima['Idade_Metabolica'])} anos")

        st.markdown("---")

        # Gráficos interativos para análise de todos os dados (2023 - 2026)
        st.subheader("📈 Evolução Histórica Completa")
        
        tab1, tab2 = st.tabs(["Evolução de Massa", "Composição de Gordura"])
        
        with tab1:
            fig_massa = px.line(df, x='Timestamp', y=['Peso_kg', 'Massa_Muscular_kg'], 
                               title="Peso vs Massa Muscular ao longo do tempo", markers=True)
            st.plotly_chart(fig_massa, use_container_width=True)
            
        with tab2:
            fig_gordura = px.line(df, x='Timestamp', y='Gordura_Total_pct', 
                                 title="Variação do Percentual de Gordura (%)", 
                                 color_discrete_sequence=['red'], markers=True)
            st.plotly_chart(fig_gordura, use_container_width=True)

        # Tabela de dados brutos processados
        with st.expander("📂 Ver Tabela de Dados Brutos"):
            st.dataframe(df.drop(columns=['Timestamp']))
    else:
        st.error("Não foram encontrados dados válidos do modelo BC-601 no ficheiro carregado.")
else:
    st.info("Por favor, carregue o ficheiro DATA1.CSV para iniciar a análise.")