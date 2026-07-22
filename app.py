import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Análise de Composição Corporal BC-601", layout="wide")

st.title("📊 Painel de Composição Corporal (BC-601)")
st.markdown("""
Esta aplicação analisa os dados históricos de bioimpedância exportados pelo dispositivo BC-601.
""")

def parse_bc601_data(file_content):
    """
    Processa o formato específico do arquivo DATA1.CSV onde chaves e valores
    estão intercalados por barras verticais (|).
    """
    records = []
    for line in file_content:
        # Limpar a linha e dividir por '|'
        parts = [p.strip() for p in line.split('|')]
        
        # O formato do BC-601 intercala etiquetas e valores (ex: DT | 11/07/2023 | Ti | 07:22:31)
        data_dict = {}
        for i in range(len(parts) - 1):
            key = parts[i]
            val = parts[i+1]
            data_dict[key] = val
            
        records.append(data_dict)
    
    df = pd.DataFrame(records)
    
    # Mapeamento de colunas importantes e conversão de tipos
    column_mapping = {
        'DT': 'Data',
        'Ti': 'Hora',
        'AG': 'Idade',
        'Wk': 'Peso_kg',
        'MI': 'IMC',
        'FW': 'Gordura_Total_pct',
        'mW': 'Massa_Muscular_kg',
        'bW': 'Massa_Ossea_kg',
        'IF': 'Gordura_Visceral',
        'rD': 'TMB_kcal',
        'rA': 'Idade_Metabolica',
        'ww': 'Agua_Corporal_pct'
    }
    
    # Filtrar apenas colunas úteis e renomear
    df = df[list(column_mapping.keys())].rename(columns=column_mapping)
    
    # Converter data e hora
    df['Data_Completa'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
    
    # Converter colunas numéricas (substituindo eventuais erros por NaN)
    numeric_cols = ['Peso_kg', 'IMC', 'Gordura_Total_pct', 'Massa_Muscular_kg', 
                    'Massa_Ossea_kg', 'Gordura_Visceral', 'TMB_kcal', 
                    'Idade_Metabolica', 'Agua_Corporal_pct']
    
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    return df.sort_values('Data_Completa')

# Carregamento do arquivo
uploaded_file = st.sidebar.file_uploader("Carregue seu arquivo DATA1.CSV", type=["csv"])

if uploaded_file is not None:
    # Ler o conteúdo como texto para o parser manual
    content = uploaded_file.getvalue().decode("utf-8").splitlines()
    df = parse_bc601_data(content)

    # --- KPIs ---
    st.subheader("Última Medição")
    last_entry = df.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Peso", f"{last_entry['Peso_kg']} kg")
    col2.metric("Gordura Corporal", f"{last_entry['Gordura_Total_pct']}%")
    col3.metric("Massa Muscular", f"{last_entry['Massa_Muscular_kg']} kg")
    col4.metric("Idade Metabólica", f"{int(last_entry['Idade_Metabolica'])} anos")

    # --- Gráficos ---
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["Tendência de Peso", "Composição", "Metabolismo"])
    
    with tab1:
        fig_peso = px.line(df, x='Data_Completa', y='Peso_kg', markers=True,
                           title="Evolução do Peso Corporal", labels={'Peso_kg': 'Peso (kg)', 'Data_Completa': 'Data'})
        st.plotly_chart(fig_peso, use_container_width=True)
        
    with tab2:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_fat = px.line(df, x='Data_Completa', y='Gordura_Total_pct', markers=True, color_discrete_sequence=['red'],
                              title="% Gordura Total")
            st.plotly_chart(fig_fat, use_container_width=True)
        with col_c2:
            fig_muscle = px.line(df, x='Data_Completa', y='Massa_Muscular_kg', markers=True, color_discrete_sequence=['green'],
                                 title="Massa Muscular (kg)")
            st.plotly_chart(fig_muscle, use_container_width=True)
            
    with tab3:
        fig_met = px.scatter(df, x='Data_Completa', y='TMB_kcal', size='Gordura_Visceral', color='Idade_Metabolica',
                             title="TMB vs Idade Metabólica (Tamanho = Gordura Visceral)")
        st.plotly_chart(fig_met, use_container_width=True)

    # --- Tabela de Dados ---
    with st.expander("Ver dados brutos processados"):
        st.dataframe(df)
else:
    st.info("Aguardando upload do arquivo DATA1.CSV para iniciar a análise.")