import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Análise Tanita BC-601", layout="wide", page_icon="⚖️")

st.title("📊 Monitor de Composição Corporal (BC-601)")
st.markdown("---")

def processar_dados_tanita(file_bytes):
    # Tenta decodificar o arquivo de forma flexível (UTF-8 ou Latin-1)
    try:
        conteudo = file_bytes.decode('utf-8', errors='ignore')
    except:
        conteudo = file_bytes.decode('latin-1', errors='ignore')
    
    linhas = conteudo.splitlines()
    registros = []
    
    # Mapeamento das siglas do dispositivo para colunas legíveis [1]
    mapeamento = {
        'DT': 'Data', 'Ti': 'Hora', 'Wk': 'Peso_kg', 'MI': 'IMC', 
        'FW': 'Gordura_Total_pct', 'mW': 'Massa_Muscular_kg', 
        'bW': 'Massa_Ossea_kg', 'IF': 'Gordura_Visceral', 
        'rD': 'TMB_kcal', 'rA': 'Idade_Metabolica', 'ww': 'Agua_Corporal_pct'
    }

    for linha in linhas:
        # Só processa linhas que contenham o identificador do modelo [1]
        if "BC-601" not in linha:
            continue
            
        # Limpeza: Remove aspas ("), chaves ({ e }) e espaços [1]
        linha_limpa = linha.replace('"', '').replace('{', '').replace('}', '').strip()
        
        # Divide a linha considerando vírgulas ou pipes como separadores
        partes = [p.strip() for p in linha_limpa.replace('|', ',').split(',') if p.strip()]
        
        dados_linha = {}
        # Busca dinâmica: localiza a sigla e captura o valor seguinte [1]
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

    # Conversão de Data e Hora para um objeto Timestamp único
    if 'Data' in df.columns and 'Hora' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Timestamp'])

    # Conversão de todas as métricas para formato numérico
    cols_numericas = [c for c in df.columns if c not in ['Data', 'Hora', 'Timestamp']]
    for col in cols_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('Timestamp')

# Interface Lateral para Upload
arquivo = st.sidebar.file_uploader("Carregue seu arquivo DATA1.CSV", type=["csv", "txt"])

if arquivo:
    df = processar_dados_tanita(arquivo.getvalue())

    if not df.empty:
        # --- BLOCO DE MÉTRICAS GERAIS ---
        inicio = df.iloc
        fim = df.iloc[-1]
        
        st.subheader(f"📅 Resumo do Período: {inicio['Data']} até {fim['Data']}")
        
        m1, m2, m3, m4 = st.columns(4)
        
        # Cálculo de variações corrigido (iloc[-1] - iloc)
        var_peso = fim['Peso_kg'] - inicio['Peso_kg']
        var_musculo = fim['Massa_Muscular_kg'] - inicio['Massa_Muscular_kg']
        
        m1.metric("Peso Atual", f"{fim['Peso_kg']} kg", f"{var_peso:.1f} kg")
        m2.metric("Massa Muscular", f"{fim['Massa_Muscular_kg']} kg", f"{var_musculo:.1f} kg")
        m3.metric("Gordura Total", f"{fim['Gordura_Total_pct']}%")
        m4.metric("Idade Metabólica", f"{int(fim['Idade_Metabolica'])} anos")

        st.markdown("---")

        # --- BLOCO DE GRÁFICOS ---
        tab1, tab2, tab3 = st.tabs(["📉 Peso e Músculo", "🔥 Gordura", "💧 Hidratação"])
        
        with tab1:
            st.plotly_chart(px.line(df, x='Timestamp', y=['Peso_kg', 'Massa_Muscular_kg'], 
                                   title="Evolução Temporal: Peso vs Massa Muscular",
                                   markers=True, labels={"value": "kg", "variable": "Métrica"}), use_container_width=True)
        
        with tab2:
            st.plotly_chart(px.line(df, x='Timestamp', y='Gordura_Total_pct', 
                                   title="Tendência de Gordura Corporal (%)",
                                   color_discrete_sequence=['red'], markers=True), use_container_width=True)
            
        with tab3:
            st.plotly_chart(px.area(df, x='Timestamp', y='Agua_Corporal_pct', 
                                   title="Nível de Água Corporal",
                                   color_discrete_sequence=['blue']), use_container_width=True)

        # --- HISTÓRICO COMPLETO ---
        with st.expander("📂 Visualizar Histórico Completo de Dados"):
            st.dataframe(df.drop(columns=['Timestamp']))
    else:
        st.error("Não foi possível processar o arquivo. Verifique se ele contém os dados do modelo BC-601.")
else:
    st.info("Aguardando o upload do arquivo DATA1.CSV para análise.")