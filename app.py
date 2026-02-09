import streamlit as st
import pandas as pd
import io
from fpdf import FPDF

# Configuração Básica - Design Nativo e Amplo
st.set_page_config(page_title="ARCANUM - Auditoria de Importação", layout="wide")

# --- CLASSE PARA GERAÇÃO DO PDF (REPLICA DO LAYOUT DANFE 607) ---
class EspelhoDANFE(FPDF):
    def header(self):
        # Quadro de Identificação do Emitente (Em branco conforme solicitado)
        self.rect(10, 10, 95, 25) 
        
        # Quadro DANFE / Número / Série [cite: 85, 88, 93]
        self.rect(105, 10, 35, 25)
        self.set_font('Arial', 'B', 10)
        self.set_xy(105, 12)
        self.cell(35, 5, 'DANFE', 0, 1, 'C')
        self.set_font('Arial', '', 6)
        self.set_x(105)
        self.cell(35, 3, 'Documento Auxiliar da', 0, 1, 'C')
        self.set_x(105)
        self.cell(35, 3, 'Nota Fiscal Eletrônica', 0, 1, 'C')
        self.set_font('Arial', 'B', 8)
        self.set_xy(105, 24)
        self.cell(35, 4, 'Nº 000.000.607', 0, 1, 'C')
        self.set_x(105)
        self.cell(35, 4, 'Série 1', 0, 1, 'C')

        # Quadro Chave de Acesso [cite: 99, 100]
        self.rect(140, 10, 60, 25)
        self.set_font('Arial', '', 6)
        self.set_xy(140, 11)
        self.cell(60, 4, 'CHAVE DE ACESSO', 0, 1, 'L')

        # Natureza da Operação [cite: 94, 95]
        self.rect(10, 35, 190, 8)
        self.set_xy(10, 35)
        self.set_font('Arial', '', 6)
        self.cell(190, 4, 'NATUREZA DA OPERAÇÃO', 0, 1, 'L')
        self.set_font('Arial', 'B', 8)
        self.set_x(10)
        self.cell(190, 4, 'COMPRA PARA COMERCIALIZACAO', 0, 1, 'L')

        # Dados do Destinatário/Remetente (Em branco conforme solicitado) [cite: 107]
        self.ln(2)
        self.set_font('Arial', 'B', 8)
        self.cell(190, 5, 'DESTINATÁRIO / REMETENTE', 1, 1, 'L')
        self.rect(10, 50, 190, 15)
        self.ln(10)

def gerar_pdf(df_final, params):
    pdf = EspelhoDANFE()
    pdf.add_page()
    
    # --- QUADRO: CÁLCULO DO IMPOSTO (REPLICA DO 607.pdf) [cite: 121] ---
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(190, 5, 'CÁLCULO DO IMPOSTO', 1, 1, 'L')
    
    fmt = lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Linha 1: Base ICMS, Vlr ICMS, Base ST, Vlr ST, V. Tot Produtos [cite: 122, 123, 145]
    pdf.set_font('Arial', '', 6)
    pdf.cell(38, 4, 'BASE DE CÁLC DO ICMS', 'LR', 0, 'L')
    pdf.cell(38, 4, 'VALOR DO ICMS', 'LR', 0, 'L')
    pdf.cell(38, 4, 'BASE DE CÁLC ICMS ST', 'LR', 0, 'L')
    pdf.cell(38, 4, 'VALOR DO ICMS ST', 'LR', 0, 'L')
    pdf.cell(38, 4, 'V. TOTAL PRODUTOS', 'LR', 1, 'L')
    
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(38, 5, fmt(params['base_icms_tot']), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(params['v_icms_recolher']), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(0.00), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(0.00), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(params['v_prod_danfe']), 'LRB', 1, 'R')
    
    # Linha 2: Frete, Seguro, PIS, Cofins, IPI, Total Nota [cite: 128, 129, 132, 139, 149, 152]
    pdf.set_font('Arial', '', 6)
    pdf.cell(31.6, 4, 'VALOR DO FRETE', 'LR', 0, 'L')
    pdf.cell(31.6, 4, 'VALOR DO SEGURO', 'LR', 0, 'L')
    pdf.cell(31.6, 4, 'VALOR DO PIS', 'LR', 0, 'L')
    pdf.cell(31.6, 4, 'VALOR COFINS', 'LR', 0, 'L')
    pdf.cell(31.6, 4, 'VALOR DO IPI', 'LR', 0, 'L')
    pdf.cell(32, 4, 'VALOR TOTAL NOTA', 'LR', 1, 'L')
    
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(31.6, 5, fmt(params['frete']), 'LRB', 0, 'R')
    pdf.cell(31.6, 5, fmt(params['seguro']), 'LRB', 0, 'R')
    pdf.cell(31.6, 5, fmt(params['pis_tot']), 'LRB', 0, 'R')
    pdf.cell(31.6, 5, fmt(params['cofins_tot']), 'LRB', 0, 'R')
    pdf.cell(31.6, 5, fmt(params['v_ipi_tot']), 'LRB', 0, 'R')
    pdf.cell(32, 5, fmt(params['v_total_nota']), 'LRB', 1, 'R')
    pdf.ln(5)

    # --- QUADRO: DADOS DO PRODUTO (REPLICA DO 607.pdf) [cite: 167] ---
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(190, 5, 'DADOS DOS PRODUTOS / SERVIÇOS', 1, 1, 'L')
    cols = ['CÓDIGO', 'DESCRIÇÃO DO PRODUTO', 'NCM/SH', 'CST', 'CFOP', 'UN', 'QTD', 'V. UNIT', 'V. TOTAL']
    w = [20, 60, 18, 10, 12, 10, 15, 22, 23]
    pdf.set_font('Arial', '', 6)
    for i, col in enumerate(cols):
        pdf.cell(w[i], 5, col, 1, 0, 'C')
    pdf.ln()

    for _, row in df_final.iterrows():
        pdf.cell(w[0], 5, "ITEM", 1)
        pdf.cell(w[1], 5, str(row.get('PRODUTO', ''))[:40], 1)
        pdf.cell(w[2], 5, str(row.get('NCM', '')), 1, 0, 'C')
        pdf.cell(w[3], 5, "100", 1, 0, 'C')
        pdf.cell(w[4], 5, "3102", 1, 0, 'C')
        pdf.cell(w[5], 5, "UN", 1, 0, 'C')
        pdf.cell(w[6], 5, f"{row.get('QTD', 0):.0f}", 1, 0, 'C')
        pdf.cell(w[7], 5, fmt(row.get('VLR_UNITARIO_BRL', 0)), 1, 0, 'R')
        pdf.cell(w[8], 5, fmt(row.get('VLR_PROD_TOTAL', 0)), 1, 0, 'R')
        pdf.ln()

    # --- DADOS ADICIONAIS [cite: 174] ---
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(190, 5, 'DADOS ADICIONAIS', 1, 1, 'L')
    pdf.set_font('Arial', '', 6)
    obs = (f"Informaçoes Complementares: Nr. DI: 2601704700 | Data DI: 28/01/2026 | "
           f"CIF: {fmt(params['cif'])} | Tx Siscomex: {fmt(params['taxa_sis'])} | "
           f"AFRMM: {fmt(params['afrmm'])} | ICMS DIFERIDO CONFORME REGULAMENTO.")
    pdf.multi_cell(190, 4, obs, 1)
    
    return bytes(pdf.output())

# --- INTERFACE STREAMLIT (RESTAURADA) ---
st.title("📜 ARCANUM")
st.write("Módulo de Auditoria de Importação - Projeto Sentinela")
st.divider()

col_cambio, col_log, col_fiscal = st.columns(3)

with col_cambio:
    st.subheader("🌐 Câmbio")
    moeda_ref = st.selectbox("Moeda", ["USD", "EUR", "CNY", "OUTRA"])
    taxa_cambio = st.number_input(f"Taxa de Câmbio", min_value=0.0001, value=5.2000, format="%.4f")

with col_log:
    st.subheader("🚛 Logística (R$)")
    v_frete = st.number_input("Frete Internacional", min_value=0.0, step=0.01)
    v_seguro = st.number_input("Seguro Internacional", min_value=0.0, step=0.01)
    v_taxas = st.number_input("Taxa Siscomex / Outras", min_value=0.0, step=0.01)
    v_afrmm = st.number_input("AFRMM Total", min_value=0.0, step=0.01)

with col_fiscal:
    st.subheader("⚖️ Fiscal")
    regime = st.selectbox("Regime", ["Lucro Real", "Lucro Presumido"])
    p_pis_aliq = 2.10 if regime == "Lucro Real" else 0.65
    p_cofins_aliq = 9.65 if regime == "Lucro Real" else 3.00
    aliq_icms = st.number_input("Alíquota ICMS (%)", value=18.0)
    perc_dif = st.number_input("Diferimento (%)", value=100.0)

st.divider()
arquivo_subido = st.file_uploader("Suba a planilha de itens", type=["xlsx"])

if arquivo_subido:
    df = pd.read_excel(arquivo_subido)
    df.columns = [c.upper().strip() for c in df.columns]
    
    # Cálculos Dinâmicos
    df['VLR_UNITARIO_BRL'] = df['VLR_UNITARIO_MOEDA'] * taxa_cambio
    df['VLR_PROD_TOTAL'] = df['QTD'] * df['VLR_UNITARIO_BRL']
    total_prods_brl = df['VLR_PROD_TOTAL'].sum()
    
    if total_prods_brl > 0:
        # Rateios e Impostos
        df['VLR_II'] = (df['VLR_PROD_TOTAL'] + (df['VLR_PROD_TOTAL']/total_prods_brl * (v_frete + v_seguro))) * (df.get('ALIQ_II', 0)/100)
        df['VLR_IPI'] = (df['VLR_PROD_TOTAL'] + df['VLR_II']) * (df.get('ALIQ_IPI', 0)/100)
        df['VLR_PIS'] = (df['VLR_PROD_TOTAL'] + (df['VLR_PROD_TOTAL']/total_prods_brl * (v_frete + v_seguro))) * (p_pis_aliq/100)
        df['VLR_COFINS'] = (df['VLR_PROD_TOTAL'] + (df['VLR_PROD_TOTAL']/total_prods_brl * (v_frete + v_seguro))) * (p_cofins_aliq/100)
        
        # Base ICMS (Cálculo por dentro conforme legislação)
        soma_base = df['VLR_PROD_TOTAL'] + (df['VLR_PROD_TOTAL']/total_prods_brl * (v_frete + v_seguro + v_taxas + v_afrmm)) + df['VLR_II'] + df['VLR_IPI'] + df['VLR_PIS'] + df['VLR_COFINS']
        df['BASE_ICMS'] = soma_base / (1 - (aliq_icms/100))
        df['VLR_ICMS_CHEIO'] = df['BASE_ICMS'] * (aliq_icms/100)
        df['VLR_ICMS_RECOLHER'] = df['VLR_ICMS_CHEIO'] * (1 - (perc_dif/100))

        params_pdf = {
            'v_prod_danfe': df['VLR_PROD_TOTAL'].sum() + df['VLR_II'].sum(),
            'frete': v_frete, 'seguro': v_seguro,
            'pis_tot': df['VLR_PIS'].sum(), 'cofins_tot': df['VLR_COFINS'].sum(),
            'v_ipi_tot': df['VLR_IPI'].sum(),
            'base_icms_tot': df['BASE_ICMS'].sum(),
            'v_icms_recolher': df['VLR_ICMS_RECOLHER'].sum(),
            'v_total_nota': df['VLR_PROD_TOTAL'].sum() + df['VLR_II'].sum() + df['VLR_IPI'].sum() + df['VLR_PIS'].sum() + df['VLR_COFINS'].sum() + v_frete + v_seguro + v_taxas + v_afrmm + df['VLR_ICMS_RECOLHER'].sum(),
            'cif': df['VLR_PROD_TOTAL'].sum() + v_frete + v_seguro,
            'taxa_sis': v_taxas, 'afrmm': v_afrmm
        }

        st.success("✅ Cálculos processados!")
        pdf_bytes = gerar_pdf(df, params_pdf)
        st.download_button("📥 Baixar DANFE (Modelo 607)", pdf_bytes, "danfe_arcanum.pdf", "application/pdf")
