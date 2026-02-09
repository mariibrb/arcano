import streamlit as st
import pandas as pd
import io

# Configuração de Identidade do Arcanum - Ecossistema Sentinela
st.set_page_config(page_title="ARCANUM - Inteligência Fiscal", layout="wide")

# Estilização Corrigida (Foco em Legibilidade e Contraste)
st.markdown("""
    <style>
    .main { background-color: #0f1116; }
    /* Títulos em Branco para leitura clara */
    h1, h2, h3 { color: #ffffff !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    /* Labels da Sidebar em Ciano para destaque suave */
    .stNumberInput label, .stRadio label, .stSelectbox label, .stCheckbox label { 
        color: #00f2ff !important; 
        font-weight: 600; 
    }
    /* Ajuste de contraste nos textos informativos */
    .stMarkdown { color: #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("# 📜 ARCANUM")
st.markdown("### *Módulo de Cálculo e Rateio de Importação*")
st.divider()

# --- PAINEL DE CONTROLE (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Parâmetros da D.I.")
    v_frete_global = st.number_input("Valor Total do Frete (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_seguro_global = st.number_input("Valor Total do Seguro (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_siscomex_global = st.number_input("Taxas Portuárias/Siscomex (R$)", min_value=0.0, step=0.01, format="%.2f")
    
    st.divider()
    st.header("🏢 Regime e Tributos Federais")

    regime = st.selectbox("Regime Tributário", ["Lucro Real (Não Cumulativo)", "Lucro Presumido (Cumulativo)"])
    
    # Alíquotas de Importação (Padrão Receita Federal)
    if "Lucro Real" in regime:
        p_pis_ini, p_cofins_ini = 2.10, 9.65
    else:
        p_pis_ini, p_cofins_ini = 0.65, 3.00

    aliq_pis = st.number_input("PIS Importação (%)", value=p_pis_ini, step=0.01)
    aliq_cofins_base = st.number_input("COFINS Importação Base (%)", value=p_cofins_ini, step=0.01)
    
    tem_majorada = st.checkbox("Aplicar Adicional COFINS (Majorada +1%)")
    aliq_majorada = 1.0 if tem_majorada else 0.0
    aliq_cofins_total = aliq_cofins_base + aliq_majorada
    
    st.info(f"Carga Federal Total: {aliq_pis + aliq_cofins_total:.2f}%")

    st.divider()
    st.header("⚖️ ICMS e Benefícios")
    
    # Ordem lógica: Diferimento primeiro
    tem_diferimento = st.radio("Haverá Diferimento de ICMS?", ("Não", "Sim"))
    aliq_icms = st.number_input("Alíquota Nominal ICMS (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.01)
    
    if tem_diferimento == "Sim":
        perc_diferimento = st.number_input("Percentual Diferido (Ex: 100 para Total)", min_value=0.0, max_value=100.0, value=100.0, step=0.1)
        aliq_diferida_calc = (perc_diferimento / 100) * aliq_icms
    else:
        aliq_diferida_calc = 0.0

    st.divider()
    st.write("SENTINELA")

# --- PROCESSAMENTO ---
st.subheader("📦 Itens da Importação")
uploaded_file = st.file_uploader("Upload da Planilha (CSV ou Excel)", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)

    with st.spinner("O Arcanum está processando os dados..."):
        col_valor = 'Valor_Aduaneiro' if 'Valor_Aduaneiro' in df.columns else df.columns[1]
        total_aduaneiro = df[col_valor].sum()

        if total_aduaneiro > 0:
            # 1. Rateio
            df['FRETE_RATEADO'] = (df[col_valor] / total_aduaneiro) * v_frete_global
            df['SEGURO_RATEADO'] = (df[col_valor] / total_aduaneiro) * v_seguro_global
            df['TAXAS_RATEADAS'] = (df[col_valor] / total_aduaneiro) * v_siscomex_global

            # 2. Impostos de Planilha
            for col in ['II', 'IPI']:
                if col not in df.columns: df[col] = 0.0
            
            # 3. PIS/COFINS (Carga de Importação)
            df['PIS_VALOR'] = df[col_valor] * (aliq_pis / 100)
            df['COFINS_VALOR'] = df[col_valor] * (aliq_cofins_total / 100)

            # 4. Base ICMS "Por Dentro"
            soma_base = (df[col_valor] + df['II'] + df['IPI'] + 
                         df['PIS_VALOR'] + df['COFINS_VALOR'] + 
                         df['FRETE_RATEADO'] + df['SEGURO_RATEADO'] + df['TAXAS_RATEADAS'])
            
            fator_icms = 1 - (aliq_icms / 100)
            df['BASE_ICMS'] = soma_base / fator_icms
            
            # 5. ICMS e Abatimento
            df['ICMS_TOTAL'] = df['BASE_ICMS'] * (aliq_icms / 100)
            df['VALOR_DIFERIDO'] = df['BASE_ICMS'] * (aliq_diferida_calc / 100)
            df['ICMS_A_RECOLHER'] = df['ICMS_TOTAL'] - df['VALOR_DIFERIDO']

            st.success("Cálculos concluídos!")
            
            exibir = [df.columns[0], col_valor, 'II', 'IPI', 'PIS_VALOR', 'COFINS_VALOR', 'BASE_ICMS', 'ICMS_A_RECOLHER']
            st.dataframe(df[exibir].style.format(precision=2), use_container_width=True)

            # Exportação Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Analise_Arcanum')
            st.download_button("📥 Baixar Excel", output.getvalue(), "arcanum_analise.xlsx")

st.sidebar.caption("Interface atualizada para alta legibilidade.")
