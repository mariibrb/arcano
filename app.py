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

    regime = st.selectbox("Regime Tributário da Empresa", ["Lucro Real (Não Cumulativo)", "Lucro Presumido (Cumulativo)"])
    
    if "Lucro Real" in regime:
        p_pis_sugerido, p_cofins_sugerido = 2.10, 9.65
    else:
        p_pis_sugerido, p_cofins_sugerido = 0.65, 3.00

    aliq_pis = st.number_input("Alíquota PIS (%)", value=p_pis_sugerido, step=0.01)
    aliq_cofins_base = st.number_input("Alíquota COFINS Base (%)", value=p_cofins_sugerido, step=0.01)
    aliq_majorada = st.number_input("Alíquota Majorada (+1%)?", min_value=0.0, max_value=10.0, value=0.0, step=1.0)
    aliq_cofins_total = aliq_cofins_base + aliq_majorada

    st.divider()

    # --- NOVA LÓGICA DE DIFERIMENTO MAIS CLARA ---
    st.header("⚖️ ICMS")
    aliq_icms = st.number_input("Alíquota ICMS da Operação (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.01)
    
    tem_diferimento = st.radio("Haverá Diferimento?", ("Não", "Sim"))
    
    if tem_diferimento == "Sim":
        # Aqui o usuário digita a porcentagem do benefício (ex: 100% para diferir tudo)
        perc_diferimento = st.number_input("Percentual do Diferimento (Ex: 100 para Total)", min_value=0.0, max_value=100.0, value=100.0, step=0.1)
        # O sistema calcula a alíquota que será efetivamente abatida
        aliq_diferida_calculada = (perc_diferimento / 100) * aliq_icms
        st.warning(f"Diferindo {perc_diferimento}% dos {aliq_icms}% (Abatimento de {aliq_diferida_calculada:.2f} pontos)")
    else:
        aliq_diferida_calculada = 0.0

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
            df['FRETE_RATEADO'] = (df[col_valor] / total_aduaneiro) * v_frete_global
            df['SEGURO_RATEADO'] = (df[col_valor] / total_aduaneiro) * v_seguro_global
            df['TAXAS_RATEADAS'] = (df[col_valor] / total_aduaneiro) * v_siscomex_global

            for col in ['II', 'IPI']:
                if col not in df.columns: df[col] = 0.0
            
            df['PIS_CALCULADO'] = df[col_valor] * (aliq_pis / 100)
            df['COFINS_CALCULADO'] = df[col_valor] * (aliq_cofins_total / 100)

            soma_base_parcial = (df[col_valor] + df['II'] + df['IPI'] + 
                                 df['PIS_CALCULADO'] + df['COFINS_CALCULADO'] + 
                                 df['FRETE_RATEADO'] + df['SEGURO_RATEADO'] + df['TAXAS_RATEADAS'])
            
            fator_icms = 1 - (aliq_icms / 100)
            df['BASE_ICMS_ARCANUM'] = soma_base_parcial / fator_icms
            
            df['ICMS_TOTAL'] = df['BASE_ICMS_ARCANUM'] * (aliq_icms / 100)
            # Valor diferido baseado na alíquota calculada pelo percentual
            df['VALOR_DIFERIDO'] = df['BASE_ICMS_ARCANUM'] * (aliq_diferida_calculada / 100)
            df['ICMS_A_RECOLHER'] = df['ICMS_TOTAL'] - df['VALOR_DIFERIDO']

            st.success("Cálculos Arcanum realizados!")
            colunas_exibir = [df.columns[0], col_valor, 'BASE_ICMS_ARCANUM', 'ICMS_TOTAL', 'VALOR_DIFERIDO', 'ICMS_A_RECOLHER']
            st.dataframe(df[colunas_exibir].style.format(precision=2), use_container_width=True)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Arcanum')
            st.download_button("📥 Baixar Planilha", buffer.getvalue(), "arcanum_analise.xlsx")
