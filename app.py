import streamlit as st
import pandas as pd
import io

# Configuração Básica - Design Nativo e Amplo
st.set_page_config(page_title="ARCANUM - Auditoria de Importação", layout="wide")

st.title("📜 ARCANUM")
st.write("Módulo de Auditoria de Importação e Geração de Espelho Fiscal - Projeto Sentinela")
st.divider()

# --- SEÇÃO 1: PARÂMETROS GLOBAIS DA D.I. ---
st.header("⚙️ 1. Configurações da D.I.")
col_cambio, col_log, col_fiscal = st.columns(3)

with col_cambio:
    st.subheader("🌐 Câmbio e Moeda")
    moeda_ref = st.selectbox("Moeda Estrangeira", ["USD", "EUR", "GBP", "CNY", "OUTRA"])
    taxa_cambio = st.number_input(f"Taxa de Câmbio ({moeda_ref} para BRL)", min_value=0.0001, value=5.0000, format="%.4f", step=0.0001)

with col_log:
    st.subheader("🚛 Logística e Taxas (R$)")
    v_frete = st.number_input("Frete Internacional Total", min_value=0.0, step=0.01, format="%.2f")
    v_seguro = st.number_input("Seguro Internacional Total", min_value=0.0, step=0.01, format="%.2f")
    v_taxas = st.number_input("Taxa Siscomex / Outras Taxas", min_value=0.0, step=0.01, format="%.2f")
    v_afrmm = st.number_input("Valor Total AFRMM (Marítimo)", min_value=0.0, step=0.01, format="%.2f")

with col_fiscal:
    st.subheader("⚖️ Fiscal e ICMS")
    regime = st.selectbox("Regime PIS/COFINS", ["Lucro Real (11,75%)", "Lucro Presumido (3,65%)"])
    
    # Alíquotas Federais
    p_pis = 2.10 if "Real" in regime else 0.65
    p_cofins = 9.65 if "Real" in regime else 3.00
    
    if st.checkbox("Aplicar Majorada (+1% COFINS)"):
        p_cofins += 1.0
        
    aliq_icms = st.number_input("Alíquota ICMS (%)", value=18.0, step=0.1)
    
    with st.expander("Configurar Diferimento"):
        tem_dif = st.radio("Haverá Diferimento?", ("Não", "Sim"), horizontal=True)
        perc_dif = 0.0
        if tem_dif == "Sim":
            perc_dif = st.number_input("Percentual Diferido (0-100%)", value=100.0, step=0.1)

st.divider()

# --- SEÇÃO 2: MODELO E UPLOAD ---
st.subheader("📋 2. Itens da Importação")
col_mod, col_up = st.columns([1, 2])

with col_mod:
    df_modelo = pd.DataFrame({
        'DI': ['26/0000001-0'],
        'ADICAO': ['001'],
        'ITEM': [1],
        'NCM': ['8517.62.77'],
        'PRODUTO': ['Exemplo de Item'],
        'QTD': [10],
        'VLR_UNITARIO_MOEDA': [300.00],
        'ALIQ_II': [14.0],
        'ALIQ_IPI': [5.0]
    })
    
    buffer_mod = io.BytesIO()
    with pd.ExcelWriter(buffer_mod, engine='openpyxl') as writer:
        df_modelo.to_excel(writer, index=False)
        
    st.download_button(
        label="📥 Baixar Planilha Modelo",
        data=buffer_mod.getvalue(),
        file_name="modelo_arcanum_di.xlsx"
    )

with col_up:
    arquivo_subido = st.file_uploader("Suba a planilha preenchida aqui", type=["xlsx"])

# --- SEÇÃO 3: CÁLCULOS E RESULTADOS ---
if arquivo_subido:
    df = pd.read_excel(arquivo_subido)
    
    with st.spinner("Processando auditoria fiscal..."):
        # 1. Normalizar nomes de colunas (Maiúsculas e sem espaços)
        df.columns = [c.upper().strip() for c in df.columns]
        
        # 2. Identificar coluna de valor unitário (Segurança contra KeyError)
        colunas_vlr_possiveis = ['VLR_UNITARIO_MOEDA', 'VLR_UNITARIO', 'VALOR_UNITARIO', 'VALOR']
        col_vlr = next((c for c in colunas_vlr_possiveis if c in df.columns), None)
        
        # Identificar coluna de quantidade
        col_qtd = next((c for c in ['QTD', 'QUANTIDADE'] if c in df.columns), None)

        if col_vlr is None or col_qtd is None:
            st.error(f"❌ Erro de Colunas: Certifique-se que a planilha tem as colunas 'QTD' e 'VLR_UNITARIO_MOEDA'.")
            st.stop()

        # 3. Conversão para BRL e Valor Total dos Itens
        df['VLR_UNITARIO_BRL'] = df[col_vlr] * taxa_cambio
        df['VLR_PROD_TOTAL'] = df[col_qtd] * df['VLR_UNITARIO_BRL']
        total_geral_prods = df['VLR_PROD_TOTAL'].sum()
        
        if total_geral_prods > 0:
            # 4. Rateios Proporcionais
            df['RAT_FRETE'] = (df['VLR_PROD_TOTAL'] / total_geral_prods) * v_frete
            df['RAT_SEGURO'] = (df['VLR_PROD_TOTAL'] / total_geral_prods) * v_seguro
            df['RAT_TAXAS'] = (df['VLR_PROD_TOTAL'] / total_geral_prods) * v_taxas
            df['RAT_AFRMM'] = (df['VLR_PROD_TOTAL'] / total_geral_prods) * v_afrmm
            
            # 5. Valor Aduaneiro (Base II, PIS e COFINS)
            df['VLR_ADUANEIRO'] = df['VLR_PROD_TOTAL'] + df['RAT_FRETE'] + df['RAT_SEGURO']
            
            # 6. Impostos Federais
            df['VLR_II'] = df['VLR_ADUANEIRO'] * (df.get('ALIQ_II', 0) / 100)
            df['VLR_IPI'] = (df['VLR_ADUANEIRO'] + df['VLR_II']) * (df.get('ALIQ_IPI', 0) / 100)
            df['VLR_PIS'] = df['VLR_ADUANEIRO'] * (p_pis / 100)
            df['VLR_COFINS'] = df['VLR_ADUANEIRO'] * (p_cofins / 100)
            
            # 7. Base ICMS "Por Dentro" (Gross-up) com Siscomex e AFRMM
            soma_componentes = (df['VLR_ADUANEIRO'] + df['VLR_II'] + df['VLR_IPI'] + 
                                df['VLR_PIS'] + df['VLR_COFINS'] + df['RAT_TAXAS'] + df['RAT_AFRMM'])
            
            fator_por_dentro = 1 - (aliq_icms / 100)
            df['BASE_ICMS'] = soma_componentes / fator_por_dentro
            
            # 8. ICMS Final e Diferimento
            df['ICMS_CHEIO'] = df['BASE_ICMS'] * (aliq_icms / 100)
            df['VLR_DIFERIDO'] = df['ICMS_CHEIO'] * (perc_dif / 100)
            df['ICMS_RECOLHER'] = df['ICMS_CHEIO'] - df['VLR_DIFERIDO']
            
            # --- EXIBIÇÃO ---
            st.divider()
            st.success("📝 Espelho da Nota Fiscal Gerado!")
            
            colunas_resumo = [
                'DI', 'ADICAO', 'ITEM', 'NCM', 'PRODUTO', 
                'VLR_ADUANEIRO', 'VLR_II', 'RAT_AFRMM', 'BASE_ICMS', 'ICMS_RECOLHER'
            ]
            
            # Filtra apenas colunas que existem para evitar erros de exibição
            cols_finais = [c for c in colunas_resumo if c in df.columns]
            st.dataframe(df[cols_finais].style.format(precision=2), use_container_width=True)

            # Exportação completa
            buffer_res = io.BytesIO()
            with pd.ExcelWriter(buffer_res, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Espelho_Arcanum')
            
            st.download_button(
                label="📥 Baixar Espelho em Excel",
                data=buffer_res.getvalue(),
                file_name="espelho_arcanum_final.xlsx"
            )
        else:
            st.error("Erro: O Valor Bruto resultou em zero. Verifique o Câmbio e a Planilha.")
