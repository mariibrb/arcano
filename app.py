import streamlit as st
import pandas as pd

# Configuração de Identidade do Arcanum - Ecossistema Sentinela
st.set_page_config(page_title="ARCANUM - Inteligência Fiscal", layout="wide")

# Estilização para manter a vibe Mariana/Sentinela
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h1 { color: #f1c40f; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("# 📜 ARCANUM")
st.markdown("### *Módulo de Cálculo e Rateio de Importação*")
st.divider()

# --- PAINEL DE CONTROLE (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Parâmetros da Importação")
    st.info("Preencha os valores globais e as alíquotas.")
    
    # Valores Globais
    v_frete_global = st.number_input("Valor Total do Frete (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_seguro_global = st.number_input("Valor Total do Seguro (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_siscomex_global = st.number_input("Taxas Portuárias/Siscomex (R$)", min_value=0.0, step=0.01, format="%.2f")
    
    st.divider()
    
    # Alíquotas Digitadas (Substituindo a barrinha)
    aliq_icms = st.number_input("Alíquota ICMS (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.1)
    aliq_diferida = st.number_input("Alíquota Diferida (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
    
    st.divider()
    st.write("Projeto Sentinela - Mariana")

# --- CORPO DA FERRAMENTA ---
st.subheader("📦 Upload dos Itens")
st.write("Suba sua planilha com: **Produto, Valor_Aduaneiro, II, IPI, PIS, COFINS**.")

uploaded_file = st.file_uploader("Arraste sua lista de produtos aqui", type=["csv", "xlsx"])

if uploaded_file:
    # Leitura do arquivo
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    with st.spinner("O Arcanum está processando o rateio e o diferimento..."):
        
        # Identificação automática da coluna de valor (assume-se 'Valor_Aduaneiro' ou a 2ª coluna)
        col_valor = 'Valor_Aduaneiro' if 'Valor_Aduaneiro' in df.columns else df.columns[1]
        total_aduaneiro = df[col_valor].sum()

        if total_aduaneiro > 0:
            # 1. Executar o Rateio
            df['FRETE_RATEADO'] = (df[col_valor] / total_aduaneiro) * v_frete_global
            df['SEGURO_RATEADO'] = (df[col_valor] / total_aduaneiro) * v_seguro_global
            df['TAXAS_RATEADAS'] = (df[col_valor] / total_aduaneiro) * v_siscomex_global

            # 2. Somar Impostos da Planilha (II, IPI, PIS, COFINS)
            cols_impostos = ['II', 'IPI', 'PIS', 'COFINS']
            # Garante que as colunas existam, se não existirem, preenche com 0
            for col in cols_impostos:
                if col not in df.columns:
                    df[col] = 0.0
            
            soma_impostos = df[cols_impostos].sum(axis=1)

            # 3. Cálculo da Base antes do ICMS
            base_parcial = (df[col_valor] + soma_impostos + 
                            df['FRETE_RATEADO'] + df['SEGURO_RATEADO'] + 
                            df['TAXAS_RATEADAS'])

            # 4. Cálculo do ICMS "Por Dentro"
            # Fórmula: Base / (1 - (Alíquota Efetiva / 100))
            # Se tem diferimento, a alíquota paga é (ICMS - Diferido)
            aliq_efetiva = aliq_icms - aliq_diferida
            fator_icms = 1 - (aliq_icms / 100) # O cálculo por dentro usa a alíquota cheia na base
            
            df['BASE_ICMS_ARCANUM'] = base_parcial / fator_icms
            df['ICMS_CHEIO'] = df['BASE_ICMS_ARCANUM'] * (aliq_icms / 100)
            
            # Cálculo do Valor Diferido e Valor a Recolher
            df['VALOR_DIFERIDO'] = df['BASE_ICMS_ARCANUM'] * (aliq_diferida / 100)
            df['ICMS_A_RECOLHER'] = df['ICMS_CHEIO'] - df['VALOR_DIFERIDO']

            # --- EXIBIÇÃO ---
            st.success("Mágica concluída! Saldo Arcanum calculado.")
            
            # Reorganizando colunas para o espelho
            cols_finais = [df.columns[0], col_valor, 'FRETE_RATEADO', 'SEGURO_RATEADO', 'TAXAS_RATEADAS', 
                           'II', 'IPI', 'PIS', 'COFINS', 'BASE_ICMS_ARCANUM', 'VALOR_DIFERIDO', 'ICMS_A_RECOLHER']
            
            st.dataframe(df[cols_finais].style.format(precision=2), use_container_width=True)

            # Exportação
            csv = df[cols_finais].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Espelho de Importação (CSV)",
                data=csv,
                file_name="arcanum_espelho_nota.csv",
                mime="text/csv",
            )
        else:
            st.warning("O valor total dos produtos está zerado. Verifique sua planilha.")
