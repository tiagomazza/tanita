import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Análise BC-601", layout="wide")

st.title("📊 Painel de Composição Corporal (BC-601)")

def parse_bc601_data(file_content):
    records = []
    for line in file_content:
        # Tenta identificar o separador (pode ser | ou ,)
        sep = '|' if '|' in line else ','
        parts = [p.strip() for p in line.split(sep) if p.strip()]
        
        # Ignora linhas que não parecem conter dados (ex: separadores de tabela)
        if len(parts) < 10 or '---' in parts:
            continue
            
        data_dict = {}
        # O formato BC-601 é sequencial: Chave, Valor, Chave, Valor...
        # Procuramos as chaves conhecidas para extrair seus valores seguintes
        keys_to_find = ['DT', 'Ti', 'AG', 'Wk', 'MI', 'FW', 'mW', 'bW', 'IF', 'rD', 'rA', 'ww']
        
        for k in keys_to_find:
            if k in parts:
                idx = parts.index(k)
                if idx + 1 < len(parts):
                    data_dict[k] = parts[idx + 1]
        
        if data_dict:
            records.append(data_dict)
    
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    
    # Mapeamento para nomes amigáveis
    column_mapping = {
        'DT': 'Data', 'Ti': 'Hora', 'AG': 'Idade', 'Wk': 'Peso_kg',
        'MI': 'IMC', 'FW': 'Gordura_Total_pct', 'mW': 'Massa_Muscular_kg',
        'bW': 'Massa_Ossea_kg', 'IF': 'Gordura_Visceral', 'rD': 'TMB_kcal',
        'rA': 'Idade_Metabolica', 'ww': 'Agua_Corporal_pct'
    }
    
    # Verifica se as colunas mínimas existem antes de renomear
    existing_cols = [c for c in column_mapping.keys() if c in df.columns]
    df = df[existing_cols].rename(columns=column_mapping)
    
    # Conversões de tipos
    if 'Data' in df.columns and 'Hora' in df.columns:
        df['Data_Completa'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
    
    numeric_cols = ['Peso_kg', 'IMC', 'Gordura_Total_pct', 'Massa_Muscular_kg', 
                    'Massa_Ossea_kg', 'Gordura_Visceral', 'TMB_kcal', 
                    'Idade_Metabolica', 'Agua_Corporal_pct']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
    return df.sort_values('Data_Completa') if 'Data_Completa' in df.columns else df

uploaded_file = st.sidebar.file_uploader("Carregue o arquivo DATA1.CSV", type=["csv", "txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8").splitlines()
    df = parse_bc601_data(content)

    if not df.empty:
        st.subheader("Evolução Recente")
        last = df.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Peso", f"{last['Peso_kg']} kg")
        c2.metric("Gordura", f"{last['Gordura_Total_pct']}%")
        c3.metric("Massa Muscular", f"{last['Massa_Muscular_kg']} kg")

        st.plotly_chart(px.line(df, x='Data_Completa', y='Peso_kg', title="Tendência de Peso"), use_container_width=True)
        st.plotly_chart(px.line(df, x='Data_Completa', y='Gordura_Total_pct', title="% Gordura"), use_container_width=True)
        
        with st.expander("Tabela Completa"):
            st.write(df)
    else:
        st.error("Não foi possível processar os dados. Verifique o formato do arquivo.")