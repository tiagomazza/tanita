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
    def parse_bc601_data(file_content):
        records = []
        for line in file_content:
            # 1. Ignora linhas de separação (ex: | ------ |) e linhas vazias
            if '---' in line or not line.strip():
                continue
                
            sep = '|' if '|' in line else ','
            parts = [p.strip() for p in line.split(sep) if p.strip()]
            
            # Filtro de segurança: registros válidos do BC-601 são longos
            if len(parts) < 15:
                continue
                
            data_dict = {}
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
        
        existing_cols = [c for c in column_mapping.keys() if c in df.columns]
        df = df[existing_cols].rename(columns=column_mapping)
        
        # 2. CONVERSÃO ROBUSTA DE DATA:
        # errors='coerce' transforma lixo em NaT (Not a Time), que limpamos depois
        if 'Data' in df.columns and 'Hora' in df.columns:
            df['Data_Completa'] = pd.to_datetime(
                df['Data'] + ' ' + df['Hora'], 
                dayfirst=True, 
                errors='coerce'
            )
            # Remove linhas onde a data falhou na conversão
            df = df.dropna(subset=['Data_Completa'])
        
        # Conversão de números (também com coerce para evitar quebras)
        numeric_cols = ['Peso_kg', 'IMC', 'Gordura_Total_pct', 'Massa_Muscular_kg', 
                        'Massa_Ossea_kg', 'Gordura_Visceral', 'TMB_kcal', 
                        'Idade_Metabolica', 'Agua_Corporal_pct']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df.sort_values('Data_Completa')