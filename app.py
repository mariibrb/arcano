import streamlit as st
import pandas as pd
import io

# Configuração de Identidade do Arcanum - Ecossistema Sentinela
st.set_page_config(page_title="ARCANUM - Inteligência Fiscal", layout="wide")

# Estilização para manter a identidade visual Mariana/Sentinela
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h1 { color: #f1c40f; font-family: 'serif'; }
    h3 { color: #ffffff; }
    .stNumberInput label, .stRadio label { color: #f1c40f !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("# 📜 ARCANUM")
st.markdown("### *Módulo de Cálculo e Rateio de Importação*")
st.divider()

# --- PAINEL DE CONTROLE (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Parâmetros Globais")
    st.info("Insira os valores totais da DI para o rateio proporcional entre os itens.")
    
    # Valores Globais da Importação
    v_frete_global = st.number_input("Valor Total do Frete (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_seguro_global = st.number_input("Valor Total do Seguro (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_siscomex_global = st.number_input("Taxas Siscomex/Aduaneiras (R$)", min_value=0.0, step=0.01, format="%.2f")
    
    st.divider()
    st.header("⚖️ Configuração de Impostos")
    
    # Alíquota Nominal de ICMS (Usada para formar a base "por dentro")
    aliq_icms = st.number_input("Alíquota ICMS Cheia (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.01)
    
    # Lógica de Diferimento Flexível
    tem_diferimento = st.radio("Existe ICMS Diferido?", ("Não", "Sim"))
    
    if tem_diferimento == "Sim":
        # Permite colocar a alíquota cheia (diferimento total) ou apenas uma parte (parcial)
        aliq_diferida = st.number_input("Alíquota do Diferimento (%)", min_value=0.0, max_value=aliq_icms, value=aliq_icms, step=0.01)
        st.caption(f"O sistema calculará {aliq_icms - aliq_diferida:.2f}% de ICMS a recolher.")
    else:
        aliq_diferida = 0.0

    st.divider()
    st.write("PROJETO SENTINELA - MARIANA")

# --- CORPO PRINCIPAL (PROCESSAMENTO) ---
st.subheader("📦 Processamento de Itens")
st.write("Faça o upload da planilha contendo as colunas: **Produto, Valor_Aduaneiro, II, IPI, PIS, COFINS**.")

uploaded_file = st.file_uploader("Arraste sua planilha de produtos aqui", type=["csv", "xlsx"])

if uploaded_file:
    # Leitura de dados
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    with st.spinner("O Arcanum está decifrando os cálculos..."):
        
        # Identificação da coluna de valor aduaneiro (base de rateio)
        # Se não encontrar o nome exato, usa a segunda coluna da planilha
        col_valor = 'Valor_Aduaneiro' if 'Valor_Aduaneiro' in df.columns else df.columns[1]
        total_aduaneiro = df[col_valor].sum()

        if total_aduaneiro > 0:
            # 1. Cálculo do Rateio Proporcional (Frete, Seguro e Taxas)
            df['FRETE_RATEADO'] = (df[col_valor] / total_aduaneiro) * v_frete_global
            df['SEGURO_RATEADO'] = (df[col_valor] / total_aduaneiro) * v_seguro_global
            df['TAXAS_RATEADAS'] = (df[col_valor] / total_aduaneiro) * v_siscomex_global

            # 2. Tratamento de Impostos (II, IPI, PIS, COFINS)
            cols_obrigatorias = ['II', 'IPI', 'PIS', 'COFINS']
            for col in cols_obrigatorias:
                if col not in df.columns:
                    df[col] = 0.0
            
            soma_impostos_outros = df[cols_obrigatorias].sum(axis=1)

            # 3. Formação da Base de Cálculo do ICMS (Cálculo "Por Dentro")
            # Base = (Soma de todos os custos e impostos) / (1 - Alíquota Nominal)
            base_antes_icms = (df[col_valor] + soma_impostos_outros + 
                               df['FRETE_RATEADO'] + df['SEGURO_RATEADO'] + 
                               df['TAXAS_RATEADAS'])
            
            fator_icms = 1 - (aliq_icms / 100)
            
            # Mesmo com diferimento, a BASE precisa ser calculada com a alíquota cheia
            df['BASE_ICMS_ARCANUM'] = base_antes_icms / fator_icms
            
            # 4. Cálculo dos Valores de ICMS (Cheio, Diferido e a Recolher)
            df['ICMS_TOTAL_CALCULADO'] = df['BASE_ICMS_ARCANUM'] * (aliq_icms / 100)
            df['VALOR_ICMS_DIFERIDO'] = df['BASE_ICMS_ARCANUM'] * (aliq_diferida / 100)
            df['ICMS_EFETIVO_A_RECOLHER'] = df['ICMS_TOTAL_CALCULADO'] - df['VALOR_ICMS_DIFERIDO']

            # --- RESULTADO FINAL ---
            st.success("Análise concluída com sucesso!")
            
            # Organização das colunas para o espelho de faturamento
            colunas_resultado = [
                df.columns[0], col_valor, 'FRETE_RATEADO', 'SEGURO_RATEADO', 'TAXAS_RATEADAS',
                'II', 'IPI', 'PIS', 'COFINS', 'BASE_ICMS_ARCANUM', 
                'ICMS_TOTAL_CALCULADO', 'VALOR_ICMS_DIFERIDO', 'ICMS_EFETIVO_A_RECOLHER'
            ]
            
            # Exibição da Tabela
            st.dataframe(df[colunas_resultado].style.format(precision=2), use_container_width=True)

            # Botão de Exportação
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df[colunas_resultado].to_excel(writer, index=False, sheet_name='Espelho Arcanum')
            
            st.download_button(
                label="📥 Baixar Memória de Cálculo (Excel)",
                data=buffer.getvalue(),
                file_name="arcanum_espelho_faturamento.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Erro: O Valor Aduaneiro total da planilha é zero. Verifique os dados.")

st.sidebar.divider()
st.sidebar.caption("Status: Arcanum Online e Operacional.")
