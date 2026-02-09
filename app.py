import streamlit as st
import pandas as pd
import io

# Configuração Básica - Design Nativo
st.set_page_config(page_title="ARCANUM - Auditoria de Importação", layout="wide")

st.title("📜 ARCANUM")
st.write("Módulo de Auditoria de Importação - Projeto Sentinela")
st.divider()

# --- SIDEBAR: PARÂMETROS ---
with st.sidebar:
    st.header("Parâmetros Globais")
    v_frete = st.number_input("Frete Total (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_seguro = st.number_input("Seguro Total (R$)", min_value=0.0, step=0.01, format="%.2f")
    v_taxas = st.number_input("Siscomex / Outras Taxas (R$)", min_value=0.0, step=0.01, format="%.2f")
    
    st.divider()
    st.header("Regime Tributário")
    regime = st.selectbox("Selecione o Regime", ["Lucro Real (11,75%)", "Lucro Presumido (3,65%)"])
    
    # Alíquotas Federais Importação (Lucro Real segue a regra de 2,10% e 9,65%)
    p_pis = 2.10 if "Real" in regime else 0.65
    p_cofins = 9.65 if "Real" in regime else 3.00
    
    if st.checkbox("Aplicar Majorada (+1% COFINS)"):
        p_cofins += 1.0

    st.divider()
    st.header("ICMS e Diferimento")
    tem_dif = st.radio("Haverá Diferimento?", ("Não", "Sim"))
    aliq_icms = st.number_input("Alíquota ICMS Operação (%)", value=18.0, step=0.1)
    
    perc_dif = 0.0
    if tem_dif == "Sim":
        perc_dif = st.number_input("Percentual do Diferimento (0-100%)", value=100.0, step=0.1)

# --- DOWNLOAD DO MODELO ---
st.subheader("1. Modelo de Planilha")
st.write("Baixe o modelo preenchido com o exemplo e utilize-o para o upload.")

# Modelo com as colunas de rastreabilidade solicitadas
df_modelo = pd.DataFrame({
    'DI': ['26/0000001-0'],
    'ADICAO': ['001'],
    'ITEM': [1],
    'NCM': ['8517.62.77'],
    'PRODUTO': ['Exemplo Item Auditoria'],
    'QTD': [10],
    'VLR_UNITARIO': [1500.00],
    'ALIQ_II': [14.0],
    'ALIQ_IPI': [5.0]
})

buffer_mod = io.BytesIO()
with pd.ExcelWriter(buffer_mod, engine='openpyxl') as writer:
    df_modelo.to_excel(writer, index=False)

st.download_button(
    label="📥 Baixar Planilha Modelo Completa",
    data=buffer_mod.getvalue(),
    file_name="modelo_arcanum_sentinela.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.divider()

# --- UPLOAD E CÁLCULOS ---
st.subheader("2. Upload e Análise")
arquivo_subido = st.file_uploader("Selecione a planilha preenchida (DI, Adição, NCM, Produto...)", type=["xlsx"])

if arquivo_subido:
    df = pd.read_excel(arquivo_subido)
    
    with st.spinner("Calculando Auditoria e Gerando Espelho..."):
        # Normalizar nomes de colunas para evitar erros de digitação
        df.columns = [c.upper() for c in df.columns]
        
        # 1. Valor Total dos Itens para base de rateio
        df['VLR_PROD_TOTAL'] = df['QTD'] * df['VLR_UNITARIO']
        total_geral_prods = df['VLR_PROD_TOTAL'].sum()
        
        if total_geral_prods > 0:
            # 2. Rateios Proporcionais (Frete, Seguro e Taxas por Item)
            df['RAT_FRETE'] = (df['VLR_PROD_TOTAL'] / total_geral_prods) * v_frete
            df['RAT_SEGURO'] = (df['VLR_PROD_TOTAL'] / total_geral_prods) * v_seguro
            df['RAT_TAXAS'] = (df['VLR_PROD_TOTAL'] / total_geral_prods) * v_taxas
            
            # 3. Valor Aduaneiro (Base para II, PIS e COFINS)
            df['VLR_ADUANEIRO'] = df['VLR_PROD_TOTAL'] + df['RAT_FRETE'] + df['RAT_SEGURO']
            
            # 4. Impostos Federais
            df['VLR_II'] = df['VLR_ADUANEIRO'] * (df.get('ALIQ_II', 0) / 100)
            df['VLR_IPI'] = (df['VLR_ADUANEIRO'] + df['VLR_II']) * (df.get('ALIQ_IPI', 0) / 100)
            df['VLR_PIS'] = df['VLR_ADUANEIRO'] * (p_pis / 100)
            df['VLR_COFINS'] = df['VLR_ADUANEIRO'] * (p_cofins / 100)
            
            # 5. Base ICMS "Por Dentro"
            # Componentes: Aduaneiro + II + IPI + PIS + COFINS + Taxas Siscomex/Portuárias
            soma_componentes = (df['VLR_ADUANEIRO'] + df['VLR_II'] + df['VLR_IPI'] + 
                                df['VLR_PIS'] + df['VLR_COFINS'] + df['RAT_TAXAS'])
            
            fator_por_dentro = 1 - (aliq_icms / 100)
            df['BASE_ICMS'] = soma_componentes / fator_por_dentro
            
            # 6. ICMS Final e Diferimento
            df['ICMS_CHEIO'] = df['BASE_ICMS'] * (aliq_icms / 100)
            df['VLR_DIFERIDO'] = df['ICMS_CHEIO'] * (perc_dif / 100)
            df['ICMS_RECOLHER'] = df['ICMS_CHEIO'] - df['VLR_DIFERIDO']
            
            # --- EXIBIÇÃO ---
            st.success("Análise Fiscal Concluída!")
            
            # Colunas organizadas para conferência rápida no Espelho
            colunas_resumo = [
                'DI', 'ADICAO', 'ITEM', 'NCM', 'PRODUTO', 
                'VLR_ADUANEIRO', 'VLR_II', 'VLR_IPI', 'BASE_ICMS', 'ICMS_RECOLHER'
            ]
            
            # Garante que colunas de texto não apareçam com decimais
            st.dataframe(df[colunas_resumo].style.format({
                'VLR_ADUANEIRO': "{:.2f}",
                'VLR_II': "{:.2f}",
                'VLR_IPI': "{:.2f}",
                'BASE_ICMS': "{:.2f}",
                'ICMS_RECOLHER': "{:.2f}"
            }), use_container_width=True)

            # Exportação do Resultado em Excel
            buffer_res = io.BytesIO()
            with pd.ExcelWriter(buffer_res, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Espelho_Arcanum')
            
            st.download_button(
                label="📥 Baixar Espelho de Importação Completo",
                data=buffer_res.getvalue(),
                file_name="espelho_arcanum_auditoria.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Erro: O Valor Total dos Produtos é zero. Verifique a coluna de Valor Unitário.")
