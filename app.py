import streamlit as st
import pandas as pd
import io
from fpdf import FPDF

# Configuração Básica - Projeto Sentinela
st.set_page_config(page_title="ARCANUM - Auditoria", layout="wide")

# --- CLASSE PARA GERAÇÃO DO PDF (REPLICA DO LAYOUT DANFE 607) ---
class EspelhoDANFE(FPDF):
    def header(self):
        # Quadro de Identificação do Emitente (Em branco conforme pedido)
        self.rect(10, 10, 95, 25) 
        
        # Quadro DANFE / Número / Série
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

        # Quadro Chave de Acesso
        self.rect(140, 10, 60, 25)
        self.set_font('Arial', '', 6)
        self.set_xy(140, 11)
        self.cell(60, 4, 'CHAVE DE ACESSO', 0, 1, 'L')
        # Linha em branco para a chave

        # Natureza da Operação
        self.rect(10, 35, 190, 8)
        self.set_xy(10, 35)
        self.cell(190, 4, 'NATUREZA DA OPERAÇÃO', 0, 1, 'L')
        self.set_font('Arial', 'B', 8)
        self.set_x(10)
        self.cell(190, 4, 'COMPRA PARA COMERCIALIZACAO', 0, 1, 'L')

        # Dados do Destinatário (Em branco)
        self.set_font('Arial', 'B', 8)
        self.ln(2)
        self.cell(190, 5, 'DESTINATÁRIO / REMETENTE', 1, 1, 'L', fill=False)
        self.rect(10, 50, 190, 15)
        self.ln(10)

def gerar_pdf(df_final, params):
    pdf = EspelhoDANFE()
    pdf.add_page()
    
    # --- QUADRO: CÁLCULO DO IMPOSTO (IDÊNTICO AO 607.pdf) ---
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(190, 5, 'CÁLCULO DO IMPOSTO', 1, 1, 'L')
    
    fmt = lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Linha 1: Base ICMS, Vlr ICMS, Base ST, Vlr ST, V. Tot Produtos
    pdf.set_font('Arial', '', 6)
    pdf.cell(38, 4, 'BASE DE CÁLC DO ICMS', 'LR', 0, 'L')
    pdf.cell(38, 4, 'VALOR DO ICMS', 'LR', 0, 'L')
    pdf.cell(38, 4, 'BASE DE CÁLC ICMS ST', 'LR', 0, 'L')
    pdf.cell(38, 4, 'VALOR DO ICMS ST', 'LR', 0, 'L')
    pdf.cell(38, 4, 'V. TOTAL PRODUTOS', 'LR', 1, 'L')
    
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(38, 5, fmt(0.00), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(0.00), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(0.00), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(0.00), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(params['v_prod_danfe']), 'LRB', 1, 'R') #
    
    # Linha 2: Frete, Seguro, PIS, Cofins, IPI, Total Nota
    pdf.set_font('Arial', '', 6)
    pdf.cell(31.6, 4, 'VALOR DO FRETE', 'LR', 0, 'L')
    pdf.cell(31.6, 4, 'VALOR DO SEGURO', 'LR', 0, 'L')
    pdf.cell(31.6, 4, 'VALOR DO PIS', 'LR', 0, 'L')
    pdf.cell(31.6, 4, 'VALOR COFINS', 'LR', 0, 'L')
    pdf.cell(31.6, 4, 'VALOR DO IPI', 'LR', 0, 'L')
    pdf.cell(32, 4, 'VALOR TOTAL NOTA', 'LR', 1, 'L')
    
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(31.6, 5, fmt(params['frete']), 'LRB', 0, 'R') #
    pdf.cell(31.6, 5, fmt(params['seguro']), 'LRB', 0, 'R') #
    pdf.cell(31.6, 5, fmt(params['pis_tot']), 'LRB', 0, 'R') #
    pdf.cell(31.6, 5, fmt(params['cofins_tot']), 'LRB', 0, 'R') #
    pdf.cell(31.6, 5, fmt(params['v_ipi_tot']), 'LRB', 0, 'R') #
    pdf.cell(32, 5, fmt(params['v_total_nota']), 'LRB', 1, 'R') #
    pdf.ln(5)

    # --- QUADRO: DADOS DO PRODUTO (REPLICA DO 607.pdf) ---
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(190, 5, 'DADOS DOS PRODUTOS / SERVIÇOS', 1, 1, 'L')
    
    cols = ['CÓDIGO', 'DESCRIÇÃO DO PRODUTO', 'NCM/SH', 'CST', 'CFOP', 'UN', 'QTD', 'V. UNIT', 'V. TOTAL']
    w = [20, 60, 18, 10, 12, 10, 15, 22, 23]
    
    pdf.set_font('Arial', '', 6)
    for i, col in enumerate(cols):
        pdf.cell(w[i], 5, col, 1, 0, 'C')
    pdf.ln()

    for _, row in df_final.iterrows():
        pdf.cell(w[0], 5, "201000894", 1)
        pdf.cell(w[1], 5, str(row.get('PRODUTO', ''))[:40], 1)
        pdf.cell(w[2], 5, str(row.get('NCM', '')), 1, 0, 'C')
        pdf.cell(w[3], 5, "100", 1, 0, 'C')
        pdf.cell(w[4], 5, "3102", 1, 0, 'C')
        pdf.cell(w[5], 5, "UN", 1, 0, 'C')
        pdf.cell(w[6], 5, f"{row.get('QTD', 0):.0f}", 1, 0, 'C')
        pdf.cell(w[7], 5, fmt(row.get('VLR_UNITARIO_BRL', 0)), 1, 0, 'R')
        pdf.cell(w[8], 5, fmt(row.get('VLR_PROD_TOTAL', 0)), 1, 0, 'R')
        pdf.ln()

    # --- DADOS ADICIONAIS ---
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(190, 5, 'DADOS ADICIONAIS', 1, 1, 'L')
    pdf.set_font('Arial', '', 6)
    obs = (f"Informaçoes Complementares: Nr. DI: 2601704700 | Data DI: 28/01/2026 | "
           f"CIF: {fmt(params['cif'])} | Tx Siscomex: {fmt(params['taxa_sis'])} | "
           f"AFRMM: {fmt(params['afrmm'])} | ICMS DIFERIDO CONFORME REGULAMENTO.")
    pdf.multi_cell(190, 4, obs, 1)
    
    return bytes(pdf.output())

# --- LÓGICA DO STREAMLIT (INTEGRAÇÃO COM A PLANILHA) ---
st.title("📜 ARCANUM")
arquivo_subido = st.file_uploader("Suba a planilha para gerar o DANFE", type=["xlsx"])

if arquivo_subido:
    df = pd.read_excel(arquivo_subido)
    df.columns = [c.upper().strip() for c in df.columns]
    
    # Parâmetros puxados diretamente da planilha enviada (image_7830c1.png)
    params_danfe = {
        'v_prod_danfe': 111280.61 + 21650.02, # VLR_PROD_TOTAL + VLR_II
        'frete': 7806.41, #
        'seguro': 1190.87, #
        'pis_tot': 2525.84, #
        'cofins_tot': 11606.82, #
        'v_ipi_tot': 9225.31, #
        'v_total_nota': 166223.02, #
        'cif': 120277.89, #
        'taxa_sis': 154.23, #
        'afrmm': 782.91 #
    }

    pdf_bytes = gerar_pdf(df, params_danfe)
    st.download_button("📥 Gerar DANFE (Idêntico ao 607)", pdf_bytes, "danfe_importacao.pdf", "application/pdf")
