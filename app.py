import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Tanita BC-601 Analytics", layout="wide", page_icon="⚖️")

st.title("📊 Monitor de Composição Corporal (BC-601)")
st.markdown("---")

def parse_tanita_sd_card(file_bytes):
    # Tenta decodificar o ficheiro (comum em cartões SD o uso de latin-1 ou utf-8)
    try:
        conteudo = file_bytes.decode('utf-8', errors='ignore')
    except:
        conteudo = file_bytes.decode('latin-1', errors='ignore')
    
    linhas = conteudo.splitlines()
    registros = []
    
    # Mapeamento das siglas técnicas encontradas no seu CSV (ex: DT, Wk, FW)
    mapeamento = {
        'DT': 'Data', 'Ti': 'Hora', 'Wk': 'Peso_kg', 'MI': 'IMC', 
        'FW': 'Gordura_Total_pct', 'mW': 'Massa_Muscular_kg', 
        'bW': 'Massa_Ossea_kg', 'IF': 'Gordura_Visceral', 
        'rD': 'TMB_kcal', 'rA': 'Idade_Metabolica', 'ww': 'Agua_Corporal_pct'
    }

    for linha in linhas:
        # Filtra apenas linhas com dados do aparelho
        if "BC-601" not in linha:
            continue
            
        # Limpeza: remove aspas e chavetas (o seu ficheiro tem { e ")
        linha_limpa = linha.replace('"', '').replace('{', '').replace('}', '').strip()
        
        # Normaliza os separadores e divide a linha
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

    # Conversão de Data e Hora para processamento temporal
    if 'Data' in df.columns and 'Hora' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Timestamp'])

    # Converte métricas para números (Peso, Gordura, etc.)
    for col in df.columns:
        if col not in ['Data', 'Hora', 'Timestamp']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('Timestamp')

# Componente de Upload
arquivo = st.sidebar.file_uploader("Carregue o ficheiro DATA1.CSV", type=["csv", "txt"])

if arquivo:
    df_analise = parse_tanita_sd_card(arquivo.getvalue())

    if not df_analise.empty:
        # CORREÇÃO DO ERRO: Uso de  e [-1] para extrair as linhas como Series
        primeira = df_analise.iloc  # Primeira medição (11/07/2023)
        ultima = df_analise.iloc[-1]   # Última medição (19/07/2026)
        
        # Agora o acesso por nome de coluna funciona perfeitamente
        st.subheader(f"📅 Período de Análise: {primeira['Data']} até {ultima['Data']}")
        
        # Painel de Indicadores
        c1, c2, c3, c4 = st.columns(4)
        
        v_peso = ultima['Peso_kg'] - primeira['Peso_kg']
        v_musculo = ultima['Massa_Muscular_kg'] - primeira['Massa_Muscular_kg']
        
        c1.metric("Peso Atual", f"{ultima['Peso_kg']} kg", f"{v_peso:.1f} kg")
        c2.metric("Massa Muscular", f"{ultima['Massa_Muscular_kg']} kg", f"{v_musculo:.1f} kg")
        c3.metric("Gordura Corporal", f"{ultima['Gordura_Total_pct']}%")
        c4.metric("Idade Metabólica", f"{int(ultima['Idade_Metabolica'])} anos")

        st.markdown("### 📈 Análise Histórica Completa")
        
        # Gráfico comparativo de Massa
        st.plotly_chart(px.line(df_analise, x='Timestamp', y=['Peso_kg', 'Massa_Muscular_kg'], 
                               title="Evolução: Peso Total vs Massa Muscular", markers=True), 
                        use_container_width=True)
        
        # Gráfico de Percentual de Gordura
        st.plotly_chart(px.line(df_analise, x='Timestamp', y='Gordura_Total_pct', 
                               title="Variação da Gordura Corporal (%)", color_discrete_sequence=['red']), 
                        use_container_width=True)

        with st.expander("📂 Ver Todos os Dados Extraídos"):
            st.dataframe(df_analise.drop(columns=['Timestamp']))
    else:
        st.error("Não foram encontrados dados compatíveis no ficheiro.")
else:
    st.info("Por favor, selecione o ficheiro DATA1.CSV no menu lateral.")