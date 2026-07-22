import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise Longitudinal BC-601", layout="wide")

def carregar_dados(file_bytes):
    conteudo = file_bytes.decode('utf-8', errors='ignore')
    linhas = conteudo.splitlines()
    registros = []
    
    # Mapeamento completo de métricas do BC-601
    mapeamento = {
        'DT': 'Data', 'Ti': 'Hora', 'Wk': 'Peso_kg', 'MI': 'IMC', 
        'FW': 'Gordura_Total_pct', 'mW': 'Massa_Muscular_kg', 
        'bW': 'Massa_Ossea_kg', 'IF': 'Gordura_Visceral', 
        'rD': 'TMB_kcal', 'rA': 'Idade_Metabolica', 'ww': 'Agua_Corporal_pct'
    }

    for linha in linhas:
        if "BC-601" not in linha: continue
        # Limpeza de caracteres especiais do formato Tanita
        linha_limpa = linha.replace('"', '').replace('{', '').replace('}', '').strip()
        partes = [p.strip() for p in linha_limpa.replace('|', ',').split(',') if p.strip()]
        
        dados_linha = {}
        for sigla, nome in mapeamento.items():
            if sigla in partes:
                idx = partes.index(sigla)
                if idx + 1 < len(partes):
                    dados_linha[nome] = partes[idx + 1]
        if dados_linha: registros.append(dados_linha)

    df = pd.DataFrame(registros)
    df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Timestamp']).sort_values('Timestamp')
    
    for col in df.columns:
        if col not in ['Data', 'Hora', 'Timestamp']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

st.title("📊 Relatório de Evolução Corporal (2023 - 2026)")

arquivo = st.sidebar.file_uploader("Carregue o arquivo DATA1.CSV", type=["csv"])

if arquivo:
    df = carregar_dados(arquivo.getvalue())
    
    if not df.empty:
        # Estatísticas de Longo Prazo
        st.header("📈 Visão Geral do Período")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Pesagens", len(df))
        col2.metric("Variação de Peso", f"{df['Peso_kg'].iloc[-1] - df['Peso_kg'].iloc:.1f} kg")
        col3.metric("Ganho de Músculo", f"{df['Massa_Muscular_kg'].iloc[-1] - df['Massa_Muscular_kg'].iloc:.1f} kg")

        # Gráfico de Tendência Central
        st.subheader("Evolução de Peso e Composição")
        fig = px.line(df, x='Timestamp', y=['Peso_kg', 'Massa_Muscular_kg'], 
                      title="Relação Peso vs. Massa Muscular", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # Análise de Gordura e Saúde
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.scatter(df, x='Timestamp', y='Gordura_Total_pct', color='Gordura_Visceral',
                                      title="% Gordura e Índice Visceral"), use_container_width=True)
        with c2:
            st.plotly_chart(px.line(df, x='Timestamp', y='Idade_Metabolica', 
                                   title="Evolução da Idade Metabólica"), use_container_width=True)

        st.divider()
        st.subheader("📋 Histórico Completo Filtrável")
        st.dataframe(df)