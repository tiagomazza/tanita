import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Tanita BC-601 Analytics", layout="wide", page_icon="⚖️")

st.title("📊 Analisador de Composição Corporal (BC-601)")
st.markdown("---")

def processar_arquivo_tanita(file_bytes):
    # Tenta decodificar o arquivo (UTF-8 é o padrão, Latin-1 como fallback)
    try:
        conteudo = file_bytes.decode('utf-8', errors='ignore')
    except:
        conteudo = file_bytes.decode('latin-1', errors='ignore')
    
    linhas = conteudo.splitlines()
    registros = []
    
    # Mapeamento das siglas do dispositivo BC-601
    mapeamento = {
        'DT': 'Data', 'Ti': 'Hora', 'Wk': 'Peso_kg', 'MI': 'IMC', 
        'FW': 'Gordura_Total_pct', 'mW': 'Massa_Muscular_kg', 
        'bW': 'Massa_Ossea_kg', 'IF': 'Gordura_Visceral', 
        'rD': 'TMB_kcal', 'rA': 'Idade_Metabolica', 'ww': 'Agua_Corporal_pct'
    }

    for linha in linhas:
        # Filtra apenas linhas que contêm o identificador do aparelho
        if "BC-601" not in linha:
            continue
            
        # Limpeza: remove aspas, chavetas e espaços desnecessários
        linha_limpa = linha.replace('"', '').replace('{', '').replace('}', '').strip()
        
        # Divide a linha considerando pipe (|) ou vírgula (,) como separadores
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

    # Conversão de Data e Hora
    if 'Data' in df.columns and 'Hora' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Timestamp'])

    # Conversão de todas as métricas para números (Peso, Gordura, Músculo, etc)
    colunas_numericas = [c for c in df.columns if c not in ['Data', 'Hora', 'Timestamp']]
    for col in colunas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Ordena por data para garantir a análise cronológica correta
    return df.sort_values('Timestamp')

# Interface de Upload
arquivo = st.sidebar.file_uploader("Carregue o seu ficheiro DATA1.CSV", type=["csv", "txt"])

if arquivo:
    df = processar_arquivo_tanita(arquivo.getvalue())

    if not df.empty:
        # CORREÇÃO DO ERRO: Extração segura da primeira e última linha
        # Usamos .iloc e .iloc[-1] para obter Series, e acessamos as colunas por nome
        primeira_pesagem = df.iloc
        ultima_pesagem = df.iloc[-1]
        
        # Exibição do Subheader com as datas extremas
        st.subheader(f"📅 Período de Análise: {primeira_pesagem['Data']} até {ultima_pesagem['Data']}")
        
        # KPIs de Destaque
        c1, c2, c3, c4 = st.columns(4)
        
        var_peso = ultima_pesagem['Peso_kg'] - primeira_pesagem['Peso_kg']
        var_musculo = ultima_pesagem['Massa_Muscular_kg'] - primeira_pesagem['Massa_Muscular_kg']
        
        c1.metric("Peso Atual", f"{ultima_pesagem['Peso_kg']} kg", f"{var_peso:.1f} kg")
        c2.metric("Massa Muscular", f"{ultima_pesagem['Massa_Muscular_kg']} kg", f"{var_musculo:.1f} kg")
        c3.metric("Gordura Corporal", f"{ultima_pesagem['Gordura_Total_pct']}%")
        c4.metric("Idade Metabólica", f"{int(ultima_pesagem['Idade_Metabolica'])} anos")

        st.markdown("---")

        # Gráficos de Evolução Completa (2023 - 2026)
        st.subheader("📈 Evolução de Longo Prazo")
        
        tab1, tab2 = st.tabs(["Composição de Massa", "Índices de Gordura"])
        
        with tab1:
            fig_massa = px.line(df, x='Timestamp', y=['Peso_kg', 'Massa_Muscular_kg'], 
                               title="Tendência de Peso vs Massa Muscular", markers=True)
            st.plotly_chart(fig_massa, use_container_width=True)
            
        with tab2:
            fig_gordura = px.line(df, x='Timestamp', y='Gordura_Total_pct', 
                                 title="Variação do Percentual de Gordura", 
                                 color_discrete_sequence=['red'], markers=True)
            st.plotly_chart(fig_gordura, use_container_width=True)

        # Tabela completa para auditoria
        with st.expander("📂 Ver Histórico Completo"):
            st.dataframe(df.drop(columns=['Timestamp']))
    else:
        st.error("O ficheiro não contém dados compatíveis com o formato do BC-601.")
else:
    st.info("Aguardando upload do ficheiro DATA1.CSV.")