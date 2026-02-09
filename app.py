import streamlit as st
import pandas as pd

# Configuração de Identidade do Arcanum
st.set_page_config(page_title="ARCANUM - Inteligência Fiscal", layout="wide")

st.markdown("# 📜 ARCANUM")
st.markdown("### *Módulo de Cálculo e Rateio de Importação*")
st.divider()

# --- PAINEL DE CONTROLE (DADOS FIXOS) ---
with st.sidebar:
    st.header("⚙️ Parâmetros da Importação")
    st.info("Preencha os valores globais para o rateio automático.")
    
    # Dados que são iguais para todos os itens daquela importação
    v_frete_global = st.number_input("Valor Total do Frete (R$)", min_value=0.0, format="%.2f")
    v_seguro_global = st.number_input("Valor Total do Seguro (R$)", min_value=0.0, format="%.2f")
    v_siscomex_global = st.number_input("Taxa Siscomex / Taxas Portuárias (R$)", min_value=0.0, format="%.2f")
    aliq_icms = st.slider("Alíquota Interna de ICMS (%)", min_value=0, max_value=25, value=18)
    
    st.divider()
    st.write("Configurado para o projeto **Sentinela**.")

# --- INPUT DE PRODUTOS (DADOS VARIÁVEIS) ---
st.subheader("📦 Upload dos Itens")
st.write("Faça o upload de uma planilha (CSV ou Excel) contendo: **Produto, NCM, Valor Aduaneiro e Impostos (II, IPI, PIS, COFINS).**")

uploaded_file = st.file_uploader("Arraste sua lista de produtos aqui", type=["csv", "xlsx"])

if uploaded_file:
    # Lógica para ler CSV ou Excel
    if uploaded_file.name.endswith('.csv'):
        df_produtos = pd.read_csv(uploaded_file)
    else:
        df_produtos = pd.read_excel(uploaded_file)

    # --- A MÁGICA DO ARCANUM (CÁLCULOS E RATEIO) ---
    with st.spinner("O Arcanum está processando o rateio..."):
        
        # 1. Calcular o Valor Total dos Produtos para base de rateio
        # Assumindo que a coluna se chama 'Valor_Aduaneiro' ou 'Valor_Produto'
        col_valor = 'Valor_Aduaneiro' if 'Valor_Aduaneiro' in df_produtos.columns else df_produtos.columns[2]
        total_aduaneiro = df_produtos[col_valor].sum()

        # 2. Executar o Rateio Proporcional
        df_produtos['FRETE_RATEADO'] = (df_produtos[col_valor] / total_aduaneiro) * v_frete_global
        df_produtos['SEGURO_RATEADO'] = (df_produtos[col_valor] / total_aduaneiro) * v_seguro_global
        df_produtos['TAXAS_RATEADAS'] = (df_produtos[col_valor] / total_aduaneiro) * v_siscomex_global

        # 3. Somatória das bases para o Cálculo "Por Dentro" do ICMS
        # Somamos: Valor Item + II + IPI + PIS + COFINS + Frete + Seguro + Taxas
        cols_impostos = ['II', 'IPI', 'PIS', 'COFINS'] # Nomes esperados na sua planilha
        
        # Soma os impostos existentes na planilha
        soma_impostos = df_produtos[cols_impostos].sum(axis=1)
        
        # Base antes do ICMS
        base_parcial = df_produtos[col_valor] + soma_impostos + df_produtos['FRETE_RATEADO'] + df_produtos['SEGURO_RATEADO'] + df_produtos['TAXAS_RATEADAS']
        
        # Cálculo final do ICMS por dentro: Base / (1 - Alíquota)
        fator_icms = 1 - (aliq_icms / 100)
        df_produtos['BASE_ICMS_ARCANUM'] = base_parcial / fator_icms
        df_produtos['VALOR_ICMS_ARCANUM'] = df_produtos['BASE_ICMS_ARCANUM'] * (aliq_icms / 100)

        # --- EXIBIÇÃO DO RESULTADO ---
        st.success("Mágica concluída! Tabela de importação gerada com sucesso.")
        
        # Formatando para exibição
        st.dataframe(df_produtos.style.format(precision=2), use_container_width=True)

        # Download do resultado pronto para o faturamento
        csv = df_produtos.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Tabela Preenchida (Excel/CSV)",
            data=csv,
            file_name="arcanum_resultado_final.csv",
            mime="text/csv",
        )
