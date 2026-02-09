import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="ARCANUM - Auditoria Fiscal", layout="wide")

# Estilização: Fundo Total Preto, Texto Verde Matrix e Branco
st.markdown("""
    <style>
    /* Fundo geral e da sidebar */
    .main, .stSidebar, .stSidebar > div { background-color: #000000 !important; }
    
    /* Títulos em Branco Puro */
    h1, h2, h3 { color: #ffffff !important; font-family: 'Courier New', Courier, monospace; font-weight: 900; }
    
    /* Labels e Inputs em Verde Neon (Estilo Terminal) */
    .stNumberInput label, .stRadio label, .stSelectbox label, .stCheckbox label { 
        color: #00ff00 !important; 
        font-size: 16px !important;
        text-transform: uppercase;
    }
    
    /* Textos Gerais */
    .stMarkdown, p, span { color: #ffffff !important; }
    
    /* Botões e Inputs */
    input { background-color: #1a1a1a !important; color: #00ff00 !important; border: 1px solid #00ff00 !important; }
    div[data-baseweb="select"] > div { background-color: #1a1a1a !important; color: #ffffff !important; }
    
    /* Tabela com borda neon */
    .stDataFrame { border: 1px solid #00ff00; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("# 📜 ARCANUM")
st.markdown("### AUDITORIA DE IMPORTAÇÃO | SENTINELA")
st.divider()

# --- SIDEBAR: PARÂMETROS ---
with st.sidebar:
    st.header("⚙️ GLOBAL")
    v_frete = st.number_input("FRETE TOTAL", min_value=0.0, step=0.01)
    v_seguro = st.number_input("SEGURO TOTAL", min_value=0.0, step=0.01)
    v_taxas = st.number_input("SISCOMEX/TAXAS", min_value=0.0, step=0.01)
    
    st.divider()
    st.header("🏢 REGIME")
    regime = st.selectbox("REGIME", ["LUCRO REAL", "LUCRO PRESUMIDO"])
    
    # Alíquotas Federais
    p_pis = 2.10 if "REAL" in regime else 0.65
    p_cofins = 9.65 if "REAL" in regime else 3.00
    
    if st.checkbox("MAJORADA (+1%)"): p_cofins += 1.0

    st.divider()
    st.header("⚖️ ICMS")
    tem_dif = st.radio("DIFERIMENTO?", ("NÃO", "SIM"))
    aliq_icms = st.number_input("ALÍQUOTA ICMS (%)", value=18.0)
    
    perc_dif = 0.0
    if tem_dif == "SIM":
        perc_dif = st.number_input("PERCENTUAL DIFERIDO (0-100)", value=100.0)

# --- DOWNLOAD MODELO ---
st.subheader("📋 1. MODELO DE IMPORTAÇÃO")
df_mod = pd.DataFrame({
    'PRODUTO': ['ITEM_01'],
    'QTD': [1],
    'VLR_UNITARIO': [1000.00],
    'ALIQ_II': [14.0],
    'ALIQ_IPI': [5.0]
})
buf_mod = io.BytesIO()
with pd.ExcelWriter(buf_mod, engine='openpyxl') as wr:
    df_mod.to_excel(wr, index=False)

st.download_button("📥 BAIXAR MODELO EXCEL", buf_mod.getvalue(), "modelo_arcanum.xlsx")
st.divider()

# --- UPLOAD E PROCESSAMENTO ---
st.subheader("📦 2. ANÁLISE DE DADOS")
up = st.file_uploader("SUBIR PLANILHA PREENCHIDA", type=["xlsx"])

if up:
    df = pd.read_excel(up)
    with st.spinner("PROCESSANDO..."):
        # Cálculos de Base
        df['VLR_PROD_TOTAL'] = df['Qtd'] * df['Valor_Unitario'] if 'Qtd' in df.columns else df['QTD'] * df['VLR_UNITARIO']
        total_geral = df['VLR_PROD_TOTAL'].sum()
        
        # Rateios
        df['RAT_FRETE'] = (df['VLR_PROD_TOTAL'] / total_geral) * v_frete
        df['RAT_SEGURO'] = (df['VLR_PROD_TOTAL'] / total_geral) * v_seguro
        df['RAT_TAXAS'] = (df['VLR_PROD_TOTAL'] / total_geral) * v_taxas
        
        # Valor Aduaneiro (Base II, PIS, COFINS)
        df['VLR_ADUANEIRO'] = df['VLR_PROD_TOTAL'] + df['RAT_FRETE'] + df['RAT_SEGURO']
        
        # Impostos
        df['VLR_II'] = df['VLR_ADUANEIRO'] * (df.get('ALIQ_II', df.get('Aliq_II', 0)) / 100)
        df['VLR_IPI'] = (df['VLR_ADUANEIRO'] + df['VLR_II']) * (df.get('ALIQ_IPI', df.get('Aliq_IPI', 0)) / 100)
        df['VLR_PIS'] = df['VLR_ADUANEIRO'] * (p_pis / 100)
        df['VLR_COFINS'] = df['VLR_ADUANEIRO'] * (p_cofins / 100)
        
        # Base ICMS Por Dentro
        soma_base = (df['VLR_ADUANEIRO'] + df['VLR_II'] + df['VLR_IPI'] + 
                     df['VLR_PIS'] + df['VLR_COFINS'] + df['RAT_TAXAS'])
        
        fator = 1 - (aliq_icms / 100)
        df['BASE_ICMS'] = soma_base / fator
        
        # ICMS Final com Diferimento
        df['ICMS_CHEIO'] = df['BASE_ICMS'] * (aliq_icms / 100)
        df['DIFERIDO_VLR'] = df['ICMS_CHEIO'] * (perc_dif / 100)
        df['ICMS_RECOLHER'] = df['ICMS_CHEIO'] - df['DIFERIDO_VLR']
        
        st.success("CÁLCULOS EXECUTADOS")
        cols = ['PRODUTO', 'VLR_ADUANEIRO', 'VLR_II', 'VLR_IPI', 'BASE_ICMS', 'ICMS_RECOLHER']
        st.dataframe(df[cols].style.format(precision=2), use_container_width=True)

        # Download do Resultado
        buf_res = io.BytesIO()
        with pd.ExcelWriter(buf_res, engine='openpyxl') as wr:
            df.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR RESULTADO COMPLETO", buf_res.getvalue(), "resultado_arcanum.xlsx")

st.sidebar.write("ESTADO: OPERACIONAL")
