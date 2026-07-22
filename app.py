import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tanita BC-601 Analytics", layout="wide")

st.title("⚖️ Analisador de Composição Corporal (BC-601)")
st.markdown("---")

def parse_tanita_v3(file_bytes):
    # Tenta decodificar o arquivo de forma flexível
    try:
        conteudo = file_bytes.decode('utf-8', errors='ignore')
    except:
        conteudo = file_bytes.decode('latin-1', errors='ignore')
    
    linhas = conteudo.splitlines()
    registros = []
    
    # Mapeamento técnico das siglas do dispositivo
    mapeamento = {
        'DT': 'Data', 'Ti': 'Hora', 'Wk': 'Peso_kg', 'MI': 'IMC', 
        'FW': 'Gordura_Total_pct', 'mW': 'Massa_Muscular_kg', 
        'bW': 'Massa_Ossea_kg', 'IF': 'Gordura_Visceral', 
        'rD': 'TMB_kcal', 'rA': 'Idade_Metabolica', 'ww': 'Agua_Corporal_pct'
    }

    for linha in linhas:
        # Só processa linhas que contenham o identificador do modelo
        if "BC-601" not in linha:
            continue
            
        # LIMPEZA CRUCIAL: Remove aspas ("), chaves ({ }) e espaços extras
        linha_limpa = linha.replace('"', '').replace('{', '').replace('}', '').strip()
        
        # Divide por vírgula ou por barra vertical (para garantir compatibilidade)
        partes = [p.strip() for p in linha_limpa.replace('|', ',').split(',') if p.strip()]
        
        dados_linha = {}
        for sigla, nome_coluna in mapeamento.items():
            if sigla in partes:
                idx = partes.index(sigla)
                if idx + 1 < len(partes):
                    # Captura o valor imediatamente após a sigla
                    dados_linha[nome_coluna] = partes[idx + 1]
        
        if dados_linha:
            registros.append(dados_linha)

    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)

    # Conversão de Data e Hora (agora sem as aspas, o Pandas reconhecerá)
    if 'Data' in df.columns and 'Hora' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Timestamp'])

    # Conversão das métricas para números
    cols_para_converter = [c for c in df.columns if c not in ['Data', 'Hora', 'Timestamp']]
    for col in cols_para_converter:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('Timestamp')

# Interface de upload
arquivo = st.sidebar.file_uploader("Arraste seu arquivo DATA1.CSV aqui", type=["csv", "txt"])

if arquivo:
    df_final = parse_tanita_v3(arquivo.getvalue())

    if not df_final.empty:
        # Exibição de Resultados
        ult = df_final.iloc[-1]
        st.success(f"Sucesso! {len(df_final)} medições processadas.")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Peso", f"{ult['Peso_kg']} kg")
        col2.metric("Gordura", f"{ult['Gordura_Total_pct']}%")
        col3.metric("Massa Muscular", f"{ult['Massa_Muscular_kg']} kg")
        col4.metric("Idade Metabólica", f"{int(ult['Idade_Metabolica'])} anos")

        st.markdown("### Tendências ao Longo do Tempo")
        
        # Gráfico de Peso e Massa Muscular
        fig1 = px.line(df_final, x='Timestamp', y=['Peso_kg', 'Massa_Muscular_kg'], 
                       title="Evolução de Peso e Músculo", markers=True)
        st.plotly_chart(fig1, use_container_width=True)
        
        # Gráfico de % de Gordura
        fig2 = px.line(df_final, x='Timestamp', y='Gordura_Total_pct', 
                       title="Variação da Gordura Corporal (%)", 
                       color_discrete_sequence=['red'], markers=True)
        st.plotly_chart(fig2, use_container_width=True)

        with st.expander("Ver Tabela de Dados"):
            st.write(df_final)
    else:
        st.error("Não foi possível ler os dados. Verifique se o arquivo não está corrompido.")