import streamlit as st
import pandas as pd
import io

# Configuração de Identidade do Arcanum - Ecossistema Sentinela
st.set_page_config(page_title="ARCANUM - Inteligência Fiscal", layout="wide")

# Estilização Mariana/Sentinela
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h1 { color: #f1c40f; font-family: 'serif'; }
    h3 { color: #ffffff; }
    .stNumberInput label, .stRadio label, .stSelectbox label { color: #f1c40f !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("# 📜 ARCANUM")
st.markdown("### *Módulo de Cálculo e Rateio de Importação*")
st.divider()

# --- PAINEL DE CONTROLE (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Parâmetros Globais")
    v_frete_global = st.number_input("Valor Total do Frete (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_seguro_global = st.number_input("Valor Total do Seguro (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_siscomex_global = st.number_input("Taxas Portuárias/Siscomex (R$)", min_value=0.0, step=0.01, format="%.2f")
    
    st.divider()
    st.header("🏢 Regime e Impostos")

    # 1. Regime Tributário (Define PIS/COFINS)
    regime = st.selectbox("Regime Tributário da Empresa", ["Lucro Real (Não Cumulativo)", "Lucro Presumido (Cumulativo)"])
    
    if "Lucro Real" in regime:
        p_pis_sugerido, p_cofins_sugerido = 1.65, 7.60
    else:
        p_pis_sugerido, p_cofins_sugerido = 0.65, 3.00

    aliq_pis = st.number_input("Alíquota PIS (%)", value=p_pis_sugerido, step=0.01)
    aliq_cofins = st.number_input("Alíquota COFINS (%)", value=p_cofins_sugerido, step=0.01)

    st.divider()

    # 2. Lógica de ICMS e Diferimento (Ordem invertida como solicitado)
    tem_diferimento = st.radio("Existe ICMS Diferido?", ("Não", "Sim"))
    
    aliq_icms = st.number_input("Alíquota ICMS Cheia (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.01)
    
    if tem_diferimento == "Sim":
        aliq_diferida = st.number_input("Alíquota do Diferimento (%)", min_value=0.0, max_value=aliq_icms, value=aliq_icms, step=0.01)
    else:
        aliq_diferida = 0.0

    st.divider()
    st.write("PROJETO SENTINELA")

# --- CORPO PRINCIPAL ---
st.subheader("📦 Processamento de Itens")
uploaded_file = st.file_uploader("Arraste sua planilha de produtos aqui", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)

    with st.spinner("O Arcanum está decifrando os cálculos..."):
        col_valor = 'Valor_Aduaneiro' if 'Valor_Aduaneiro' in df.columns else df.columns[1]
        total_aduaneiro = df[col_valor].sum()

        if total_aduaneiro > 0:
            # Rateio
            df['FRETE_RATEADO'] = (df[col_valor] / total_aduaneiro) * v_frete_global
            df['SEGURO_RATEADO'] = (df[col_valor] / total_aduaneiro) * v_seguro_global
            df['TAXAS_RATEADAS'] = (df[col_valor] / total_aduaneiro) * v_siscomex_global

            # Impostos Base (II e IPI vêm da planilha, PIS/COFINS calculamos se estiverem zerados)
            for col in ['II', 'IPI']:
                if col not in df.columns: df[col] = 0.0
            
            # Cálculo de PIS e COFINS baseado no regime escolhido (caso não venha na planilha)
            df['PIS_CALCULADO'] = df[col_valor] * (aliq_pis / 100)
            df['COFINS_CALCULADO'] = df[col_valor] * (aliq_cofins / 100)

            # Base de Cálculo ICMS (Cálculo "Por Dentro")
            # Inclui: Valor Item + II + IPI + PIS + COFINS + Frete + Seguro + Taxas
            soma_base_parcial = (df[col_valor] + df['II'] + df['IPI'] + 
                                 df['PIS_CALCULADO'] + df['COFINS_CALCULADO'] + 
                                 df['FRETE_RATEADO'] + df['SEGURO_RATEADO'] + df['TAXAS_RATEADAS'])
            
            fator_icms = 1 - (aliq_icms / 100)
            df['BASE_ICMS_ARCANUM'] = soma_base_parcial / fator_icms
            
            # ICMS e Diferimento
            df['ICMS_TOTAL'] = df['BASE_ICMS_ARCANUM'] * (aliq_icms / 100)
            df['VALOR_DIFERIDO'] = df['BASE_ICMS_ARCANUM'] * (aliq_diferida / 100)
            df['ICMS_A_RECOLHER'] = df['ICMS_TOTAL'] - df['VALOR_DIFERIDO']

            # Exibição
            st.success("Cálculos Arcanum realizados!")
            colunas_exibir = [df.columns[0], col_valor, 'II', 'IPI', 'PIS_CALCULADO', 'COFINS_CALCULADO', 'BASE_ICMS_ARCANUM', 'ICMS_A_RECOLHER']
            st.dataframe(df[colunas_exibir].style.format(precision=2), use_container_width=True)

            # Exportação Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Arcanum_Import')
            st.download_button("📥 Baixar Planilha Completa", buffer.getvalue(), "arcanum_import.xlsx")
