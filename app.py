import streamlit as st
import pandas as pd
import io
from fpdf import FPDF

# Configuração Básica - Projeto Sentinela
st.set_page_config(page_title="ARCANUM - Auditoria de Importação", layout="wide")

# --- CLASSE PARA GERAÇÃO DO PDF (REPLICA DO LAYOUT DANFE 607) ---
class EspelhoDANFE(FPDF):
    def header(self):
        # Quadro de Identificação do Emitente (Em branco)
        self.rect(10, 10, 95, 25) 
        
        # [cite_start]Quadro DANFE / Número 0 / Série 0 [cite: 85, 93, 98]
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
        self.cell(35, 4, 'Nº 000.000.000', 0, 1, 'C') 
        self.set_x(105)
        self.cell(35, 4, 'Série 0', 0, 1, 'C') 

        # [cite_start]Quadro Chave de Acesso [cite: 100]
        self.rect(140, 10, 60, 25)
        self.set_font('Arial', '', 6)
        self.set_xy(140, 11)
        self.cell(60, 4, 'CHAVE DE ACESSO', 0, 1, 'L')

        # [cite_start]Natureza da Operação [cite: 94, 95]
        self.rect(10, 35, 190, 8)
        self.set_xy(10, 35)
        self.set_font('Arial', '', 6)
        self.cell(190, 4, 'NATUREZA DA OPERAÇÃO', 0, 1, 'L')
        self.set_font('Arial', 'B', 8)
        self.set_x(10)
        self.cell(190, 4, 'COMPRA PARA COMERCIALIZACAO', 0, 1, 'L')

        # [cite_start]Dados do Destinatário/Remetente [cite: 107-120]
        self.ln(2)
        self.set_font('Arial', 'B', 8)
        self.cell(190, 5, 'DESTINATÁRIO / REMETENTE', 1, 1, 'L')
        self.rect(10, 50, 190, 15)
        self.ln(10)

def gerar_pdf(df_final, params):
    pdf = EspelhoDANFE()
    pdf.add_page()
    
    # [cite_start]--- QUADRO: CÁLCULO DO IMPOSTO (DISTRIBUIÇÃO ACORDADA) [cite: 121-152] ---
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(190, 5, 'CÁLCULO DO IMPOSTO', 1, 1, 'L')
    
    fmt = lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Linha 1: Bases e Total Produtos (Produtos + II)
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
    
    # [cite_start]Linha 2: Frete, Seguro, PIS, Cofins, IPI, Total Nota [cite: 128, 129, 132, 139, 149, 152]
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

    # [cite_start]--- QUADRO: DADOS DO PRODUTO [cite: 167] ---
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

    # [cite_start]--- DADOS ADICIONAIS [cite: 174, 175] ---
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(190, 5, 'DADOS ADICIONAIS', 1, 1, 'L')
    pdf.set_font('Arial', '', 6)
    obs = (f"Informacoes Complementares: CIF: {fmt(params['cif'])} | Tx Siscomex: {fmt(params['taxa_sis'])} | "
           f"AFRMM: {fmt(params['afrmm'])} | ICMS DIFERIDO NO VALOR DE R$ {fmt(params['v_icms_diferido'])}.")
    pdf.multi_cell(190, 4, obs, 1)
    
    return bytes(pdf.output())

# --- INTERFACE STREAMLIT (CAMPOS ZERADOS) ---
st.title("📜 ARCANUM")
st.divider()

col_cambio, col_log, col_fiscal = st.columns(3)
with col_cambio:
    taxa_cambio = st.number_input("Taxa de Câmbio", min_value=0.0, value=0.0, format="%.4f")
with col_log:
    v_frete = st.number_input("Frete Internacional", min_value=0.0, value=0.0, step=0.01)
    v_seguro = st.number_input("Seguro Internacional", min_value=0.0, value=0.0, step=0.01)
    v_taxas = st.number_input("Taxas Siscomex", min_value=0.0, value=0.0, step=0.01)
    v_afrmm = st.number_input("AFRMM Total", min_value=0.0, value=0.0, step=0.01)
with col_fiscal:
    regime = st.selectbox("Regime PIS/COFINS", ["Lucro Real", "Lucro Presumido"])
    aliq_icms = st.number_input("Alíquota ICMS (%)", value=18.0)
    tem_dif = st.radio("Diferimento?", ("Sim", "Não"), horizontal=True)
    perc_dif = st.number_input("Percentual Diferido (%)", value=100.0) if tem_dif == "Sim" else 0.0

st.divider()

# --- SEÇÃO 2: MODELO E UPLOAD ---
st.subheader("📋 2. Itens da Importação")
col_mod, col_up = st.columns([1, 2])
with col_mod:
    df_modelo = pd.DataFrame({'PRODUTO': ['ITEM'], 'NCM': ['0000.00.00'], 'QTD': [0], 'VLR_UNITARIO_MOEDA': [0.0], 'ALIQ_II': [0.0], 'ALIQ_IPI': [0.0]})
    buffer_mod = io.BytesIO()
    with pd.ExcelWriter(buffer_mod, engine='openpyxl') as writer: df_modelo.to_excel(writer, index=False)
    st.download_button(label="📥 Baixar Planilha Modelo", data=buffer_mod.getvalue(), file_name="modelo_arcanum.xlsx")
with col_up:
    arquivo_subido = st.file_uploader("Suba a planilha", type=["xlsx"])

# --- SEÇÃO 3: CÁLCULOS DINÂMICOS ---
if arquivo_subido:
    df = pd.read_excel(arquivo_subido)
    df.columns = [c.upper().strip() for c in df.columns]
    
    col_vlr = next((c for c in ['VLR_UNITARIO_MOEDA', 'VLR_UNITARIO'] if c in df.columns), None)
    col_qtd = next((c for c in ['QTD', 'QUANTIDADE'] if c in df.columns), None)

    if col_vlr and col_qtd and taxa_cambio > 0:
        df['VLR_UNITARIO_BRL'] = df[col_vlr] * taxa_cambio
        df['VLR_PROD_TOTAL'] = df[col_qtd] * df['VLR_UNITARIO_BRL']
        total_prods_brl = df['VLR_PROD_TOTAL'].sum()
        
        p_pis = 2.10 if regime == "Lucro Real" else 0.65
        p_cof = 9.65 if regime == "Lucro Real" else 3.00
        
        v_ii_tot = df['VLR_PROD_TOTAL'].sum() * 0.14 
        v_ipi_tot = (df['VLR_PROD_TOTAL'].sum() + v_ii_tot) * 0.065 
        pis_tot = total_prods_brl * (p_pis/100)
        cof_tot = total_prods_brl * (p_cof/100)
        
        base_icms = (total_prods_brl + v_frete + v_seguro + v_taxas + v_afrmm + v_ii_tot + v_ipi_tot + pis_tot + cof_tot) / (1 - (aliq_icms/100))
        icms_cheio = base_icms * (aliq_icms/100)
        v_icms_diferido = icms_cheio * (perc_dif/100)
        v_icms_recolher = icms_cheio - v_icms_diferido

        params_pdf = {
            'v_prod_danfe': total_prods_brl + v_ii_tot,
            'frete': v_frete, 'seguro': v_seguro,
            'pis_tot': pis_tot, 'cofins_tot': cof_tot,
            'v_ipi_tot': v_ipi_tot, 'base_icms_tot': base_icms,
            'v_icms_recolher': v_icms_recolher, 'v_icms_diferido': v_icms_diferido,
            'v_total_nota': total_prods_brl + v_ii_tot + v_ipi_tot + pis_tot + cof_tot + v_frete + v_seguro + v_taxas + v_afrmm + v_icms_recolher,
            'cif': total_prods_brl + v_frete + v_seguro, 'taxa_sis': v_taxas, 'afrmm': v_afrmm
        }

        st.success("✅ Cálculos realizados!")
        pdf_bytes = gerar_pdf(df, params_pdf)
        st.download_button("📥 Baixar DANFE (Padrão Acordado)", pdf_bytes, "danfe_arcanum.pdf", "application/pdf")
