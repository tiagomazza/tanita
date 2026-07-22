import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise Tanita BC-601", layout="wide")
st.title("📊 Painel de Bioimpedância BC-601")

def processar_arquivo(file_bytes):
    # Tenta diferentes codificações comuns em arquivos de dispositivos
    for encoding in ['utf-8', 'utf-16', 'latin-1', 'cp1252']:
        try:
            texto = file_bytes.decode(encoding).splitlines()
            if len(texto) > 0:
                break
        except:
            continue
    else:
        return pd.DataFrame()

    registros = []
    mapeamento = {
        'DT': 'Data', 'Ti': 'Hora', 'AG': 'Idade', 'Wk': 'Peso_kg',
        'MI': 'IMC', 'FW': 'Gordura_Total_pct', 'mW': 'Massa_Muscular_kg',
        'bW': 'Massa_Ossea_kg', 'IF': 'Gordura_Visceral', 'rD': 'TMB_kcal',
        'rA': 'Idade_Metabolica', 'ww': 'Agua_Corporal_pct'
    }

    for linha in texto:
        if not linha.strip() or '---' in linha:
            continue
            
        # Detecta automaticamente se o separador é | ou ,
        sep = '|' if '|' in linha else ','
        partes = [p.strip() for p in linha.split(sep) if p.strip()]
        
        dados_linha = {}
        for sigla, nome in mapeamento.items():
            if sigla in partes:
                idx = partes.index(sigla)
                if idx + 1 < len(partes):
                    dados_linha[nome] = partes[idx + 1]
        
        if dados_linha:
            registros.append(dados_linha)

    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)

    # Conversão de Data e Hora
    if 'Data' in df.columns and 'Hora' in df.columns:
        df['Timestamp'] = pd.to_datetime(
            df['Data'] + ' ' + df['Hora'], 
            dayfirst=True, 
            errors='coerce'
        )
        df = df.dropna(subset=['Timestamp'])

    # Conversão de Números
    for col in df.columns:
        if col not in ['Data', 'Hora', 'Timestamp']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('Timestamp')

arquivo = st.sidebar.file_uploader("Carregue o arquivo DATA1.CSV", type=["csv", "txt"])

if arquivo:
    df = processar_arquivo(arquivo.getvalue())

    if not df.empty:
        # Métricas de destaque
        u = df.iloc[-1]
        st.subheader(f"Última medição em {u['Timestamp'].strftime('%d/%m/%Y')}")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Peso", f"{u['Peso_kg']} kg")
        c2.metric("Gordura", f"{u['Gordura_Total_pct']}%")
        c3.metric("Músculo", f"{u['Massa_Muscular_kg']} kg")
        c4.metric("Idade Met.", f"{int(u['Idade_Metabolica'])} anos")

        # Gráficos
        st.plotly_chart(px.line(df, x='Timestamp', y=['Peso_kg', 'Massa_Muscular_kg'], 
                               title="Evolução de Peso e Massa Muscular", markers=True), use_container_width=True)
        
        st.plotly_chart(px.line(df, x='Timestamp', y='Gordura_Total_pct', 
                               title="% de Gordura Corporal", color_discrete_sequence=['red'], markers=True), use_container_width=True)

        with st.expander("Ver Histórico Completo"):
            st.dataframe(df)
    else:
        st.error("Erro: O formato interno do arquivo não foi reconhecido. Certifique-se de que é o arquivo DATA1.CSV original do cartão SD.")
