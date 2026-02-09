import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="ARCANUM - Inteligência Fiscal", layout="wide")

# Estilização: Fundo Preto, Texto Branco e Ciano Forte (Sem tons pastel)
st.markdown("""
    <style>
    .main { background-color: #000000; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 800; }
    .stNumberInput label, .stRadio label, .stSelectbox label, .stCheckbox label { 
        color: #00ffff !important; 
        font-size: 18px !important;
        font-weight: bold !important;
    }
    .stMarkdown, p { color: #ffffff !important; font-size: 16px; }
    stDataFrame { border: 2px solid #00ffff; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("# 📜 ARCANUM")
st.markdown("### *Módulo de Auditoria de Importação*")
st.divider()

# --- PAINEL DE CONTROLE (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ PARÂMETROS GLOBAIS")
    v_frete_global = st.number_input("Frete Total (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_seguro_global = st.number_input("Seguro Total (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_siscomex_global = st.number_input("Siscomex/Taxas (R$)", min_value=0.0, step=0.01, format="%.2f")
    
    st.divider()
    st.header("🏢 REGIME E PIS/COFINS")
    regime = st.selectbox("Regime Empresa", ["Lucro Real (11,75%)", "Lucro Presumido (3,65%)"])
    aliq_pis = 2.10 if "Real" in regime else 0.65
    aliq_cofins = 9.65 if "Real" in regime else 3.00
    
    tem_majorada = st.checkbox("Majorada (+1% COFINS)")
    if tem_majorada: aliq_cofins += 1.0

    st.divider()
    st.header("⚖️ ICMS E DIFERIMENTO")
    tem_dif = st.radio("Diferimento?", ("Não", "Sim"))
    aliq_icms = st.number_input("Alíquota ICMS (%)", value=18.0)
    perc_dif = st.number_input("% do Diferimento (Ex: 100)", value=100.0) if tem_dif == "Sim" else 0.0

# --- MODELO DE PLANILHA MINIMALISTA ---
st.subheader("📋 1. Baixe o Modelo Minimalista")
modelo_min = pd.DataFrame({
    'Produto': ['Item A'],
    'NCM': ['8517.62.77'],
    'Qtd': [10],
    'Valor_Unitario': [100.00],
    'Aliq_II': [14.0],  # Você preenche se quiser, se não o Arcanum usa 0
    'Aliq_IPI': [5.0]    # Você preenche se quiser
})

buffer_mod = io.BytesIO()
with pd.ExcelWriter(buffer_mod, engine='openpyxl') as writer:
    modelo_min.to_excel(writer, index=False)

st.download_button("📥 Baixar Planilha Exemplo", buffer_mod.getvalue(), "modelo_arcanum.xlsx")

st.divider()

# --- UPLOAD E MÁGICA ---
st.subheader("📦 2. Upload e Resultado")
up = st.file_uploader("Suba sua planilha", type=["xlsx"])

if up:
    df = pd.read_excel(up)
    with st.spinner("Calculando..."):
        # Cálculo do Valor Aduaneiro por Item
        df['VLR_PROD_TOTAL'] = df['Qtd'] * df['Valor_Unitario']
        total_prods = df['VLR_PROD_TOTAL'].sum()
        
        # Rateio
        df['FRETE_RAT'] = (df['VLR_PROD_TOTAL'] / total_prods) * v_frete_global
        df['SEGURO_RAT'] = (df['VLR_PROD_TOTAL'] / total_prods) * v_seguro_global
        df['TAXA_RAT'] = (df['VLR_PROD_TOTAL'] / total_prods) * v_siscomex_global
        
        # Valor Aduaneiro (Base para II, PIS, COFINS)
        df['VLR_ADUANEIRO'] = df['VLR_PROD_TOTAL'] + df['FRETE_RAT'] + df['SEGURO_RAT']
        
        # Impostos Federais
        df['II_VLR'] = df['VLR_ADUANEIRO'] * (df.get('Aliq_II', 0) / 100)
        df['IPI_VLR'] = (df['VLR_ADUANEIRO'] + df['II_VLR']) * (df.get('Aliq_IPI', 0) / 100)
        df['PIS_VLR'] = df['VLR_ADUANEIRO'] * (aliq_pis / 100)
        df['COFINS_VLR'] = df['VLR_ADUANEIRO'] * (aliq_cofins / 100)
        
        # Base ICMS (Por Dentro)
        # Itens + II + IPI + PIS + COFINS + Taxas / (1 - Aliq)
        soma_base = (df['VLR_ADUANEIRO'] + df['II_VLR'] + df['IPI_VLR'] + 
                     df['PIS_VLR'] + df['COFINS_VLR'] + df['TAXA_RAT'])
        
        fator = 1 - (aliq_icms / 100)
        df['BASE_ICMS'] = soma_base / fator
        df['ICMS_RECOLHER'] = (df['BASE_ICMS'] * (aliq_icms / 100)) * (1 - (perc_dif / 100))
        
        st.success("Análise Concluída!")
        st.dataframe(df[['Produto', 'VLR_ADUANEIRO', 'II_VLR', 'IPI_VLR', 'BASE_ICMS', 'ICMS_RECOLHER']].style.format(precision=2))
