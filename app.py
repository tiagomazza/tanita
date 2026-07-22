import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Analise Tanita BC-601", layout="wide")

st.title("⚖️ Analisador de Composição Corporal BC-601")
st.info("Carregue o arquivo DATA1.CSV original do seu cartão SD.")

def robust_parse_tanita(file_bytes):
    # Tenta ler o arquivo de forma bruta para evitar erros de encoding
    try:
        content = file_bytes.decode('utf-16') if b'\xff\xfe' in file_bytes[:2] else file_bytes.decode('utf-8', errors='ignore')
    except:
        content = file_bytes.decode('latin-1', errors='ignore')

    lines = content.splitlines()
    registros = []
    
    # Mapeamento técnico baseado no manual do BC-601
    mapeamento = {
        'DT': 'Data', 'Ti': 'Hora', 'Wk': 'Peso_kg', 'MI': 'IMC', 
        'FW': 'Gordura_Total_pct', 'mW': 'Massa_Muscular_kg', 
        'bW': 'Massa_Ossea_kg', 'IF': 'Gordura_Visceral', 
        'rD': 'TMB_kcal', 'rA': 'Idade_Metabolica', 'ww': 'Agua_Corporal_pct'
    }

    for line in lines:
        # Só processa se a linha contiver o identificador do aparelho
        if "BC-601" not in line:
            continue
            
        # Limpa a linha e divide pelo pipe
        parts = [p.strip() for p in line.split('|') if p.strip()]
        
        dados_linha = {}
        # Busca cada métrica pelo nome da sigla
        for sigla, nome in mapeamento.items():
            if sigla in parts:
                idx = parts.index(sigla)
                if idx + 1 < len(parts):
                    dados_linha[nome] = parts[idx + 1]
        
        if dados_linha:
            registros.append(dados_linha)

    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)

    # Conversão de Data e Hora para o eixo do gráfico
    if 'Data' in df.columns and 'Hora' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Timestamp'])

    # Converte todas as métricas para números
    cols_numericas = ['Peso_kg', 'IMC', 'Gordura_Total_pct', 'Massa_Muscular_kg', 
                      'Massa_Ossea_kg', 'Gordura_Visceral', 'TMB_kcal', 
                      'Idade_Metabolica', 'Agua_Corporal_pct']
    
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('Timestamp')

arquivo = st.sidebar.file_uploader("Selecione o arquivo DATA1.CSV", type=["csv", "txt"])

if arquivo:
    df = robust_parse_tanita(arquivo.getvalue())

    if not df.empty:
        # Exibição de KPIs da última pesagem
        ultimo = df.iloc[-1]
        st.success(f"Dados carregados com sucesso! {len(df)} medições encontradas.")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Peso Atual", f"{ultimo['Peso_kg']} kg")
        c2.metric("Gordura Total", f"{ultimo['Gordura_Total_pct']}%")
        c3.metric("Massa Muscular", f"{ultimo['Massa_Muscular_kg']} kg")
        c4.metric("Idade Metabólica", f"{int(ultimo['Idade_Metabolica'])} anos")

        # Gráficos Interativos
        st.markdown("### 📈 Evolução Temporal")
        
        tab1, tab2 = st.tabs(["Peso e Gordura", "Massa Muscular"])
        
        with tab1:
            fig1 = px.line(df, x='Timestamp', y=['Peso_kg', 'Gordura_Total_pct'], 
                          title="Tendência de Peso e Gordura Corporal", markers=True)
            st.plotly_chart(fig1, use_container_width=True)
            
        with tab2:
            fig2 = px.line(df, x='Timestamp', y='Massa_Muscular_kg', 
                          title="Evolução da Massa Muscular (kg)", color_discrete_sequence=['green'], markers=True)
            st.plotly_chart(fig2, use_container_width=True)

        with st.expander("📂 Ver dados brutos extraídos"):
            st.dataframe(df)
    else:
        st.error("Não foi possível encontrar registros de pesagem. O arquivo parece estar vazio ou em formato incompatível.")
        # Debug para o usuário
        st.write("Prévia do conteúdo detectado:")
        st.code(arquivo.getvalue()[:500].decode('utf-8', errors='replace'))