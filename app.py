import streamlit as st
import pandas as pd
import io
from fpdf import FPDF

# Configuração Básica - Projeto Sentinela
st.set_page_config(page_title="ARCANUM - Auditoria de Importação", layout="wide")

# --- CLASSE PARA GERAÇÃO DO PDF (REPLICA DO MODELO 607) ---
class EspelhoDANFE(FPDF):
    def header(self):
        # Quadro Emitente e DANFE
        self.rect(10, 10, 95, 25) 
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

        # Quadro Chave de Acesso
        self.rect(140, 10, 60, 25)
        self.rect(10, 35, 190, 8)
        self.set_xy(10, 35)
        self.set_font('Arial', '', 6)
        self.cell(190, 4, 'NATUREZA DA OPERAÇÃO', 0, 1, 'L')
        self.set_font('Arial', 'B', 8)
        self.set_x(10)
        self.cell(190, 4, 'COMPRA PARA COMERCIALIZACAO', 0, 1, 'L')

        # Destinatário
        self.ln(2)
        self.set_font('Arial', 'B', 8)
        self.cell(190, 5, 'DESTINATÁRIO / REMETENTE', 1, 1, 'L')
        self.rect(10, 50, 190, 15)
        self.ln(10)

def gerar_pdf(df_final, params):
    pdf = EspelhoDANFE()
    pdf.add_page()
    
    fmt = lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # --- QUADRO: CÁLCULO DO IMPOSTO ---
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(190, 5, 'CÁLCULO DO IMPOSTO', 1, 1, 'L')
    
    pdf.set_font('Arial', '', 6)
    pdf.cell(38, 4, 'BASE DE CÁLC DO ICMS', 'LR', 0, 'L')
    pdf.cell(38, 4, 'VALOR DO ICMS', 'LR', 0, 'L')
    pdf.cell(38, 4, 'BASE DE CÁLC ICMS ST', 'LR', 0, 'L')
    pdf.cell(38, 4, 'VALOR DO ICMS ST', 'LR', 0, 'L')
    pdf.cell(38, 4, 'V. TOTAL PRODUTOS', 'LR', 1, 'L')
    
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(38, 5, fmt(params['base_icms_header']), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(params['v_icms_header']), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(0.00), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(0.00), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(params['v_prod_composto']), 'LRB', 1, 'R')
    
    pdf.set_font('Arial', '', 6)
    pdf.cell(38, 4, 'VALOR DO FRETE', 'LR', 0, 'L')
    pdf.cell(38, 4, 'VALOR DO SEGURO', 'LR', 0, 'L')
    pdf.cell(38, 4, 'OUTRAS DESPESAS', 'LR', 0, 'L') 
    pdf.cell(38, 4, 'VALOR DO IPI', 'LR', 0, 'L') 
    pdf.cell(38, 4, 'VALOR TOTAL NOTA', 'LR', 1, 'L')
    
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(38, 5, fmt(params['frete']), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(params['seguro']), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(params['afrmm']), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(params['v_ipi_tot']), 'LRB', 0, 'R')
    pdf.cell(38, 5, fmt(params['v_total_nota']), 'LRB', 1, 'R')
    pdf.ln(5)

    # --- QUADRO: DADOS DO PRODUTO ---
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(190, 5, 'DADOS DOS PRODUTOS / SERVIÇOS', 1, 1, 'L')
    
    cols = [
        ('CÓDIGO', 15), ('DESCRIÇÃO', 45), ('NCM', 15), ('CST', 8), ('CFOP', 10), 
        ('QTD', 10), ('V.UNIT', 15), ('V.TOT', 15), ('BC.ICMS', 15), ('V.ICMS', 14), 
        ('V.IPI', 13), ('%ICMS', 10), ('%IPI', 10)
    ]
    
    pdf.set_font('Arial', '', 5)
    for txt, w in cols:
        pdf.cell(w, 5, txt, 1, 0, 'C')
    pdf.ln()

    for _, row in df_final.iterrows():
        pdf.cell(15, 5, "ITEM", 1)
        pdf.cell(45, 5, str(row.get('PRODUTO', ''))[:30], 1)
        pdf.cell(15, 5, str(row.get('NCM', '')), 1, 0, 'C')
        pdf.cell(8, 5, params['cst_calculado'], 1, 0, 'C')
        pdf.cell(10, 5, "3102", 1, 0, 'C')
        pdf.cell(10, 5, f"{row.get('QTD', 0):.0f}", 1, 0, 'C')
        pdf.cell(15, 5, fmt(row.get('VLR_UNITARIO_BRL', 0)), 1, 0, 'R')
        pdf.cell(15, 5, fmt(row.get('VLR_PROD_TOTAL', 0)), 1, 0, 'R')
        pdf.cell(15, 5, fmt(row.get('BC_ICMS_ITEM', 0)), 1, 0, 'R')
        pdf.cell(14, 5, fmt(row.get('V_ICMS_ITEM', 0)), 1, 0, 'R')
        pdf.cell(13, 5, fmt(row.get('VLR_IPI_ITEM', 0)), 1, 0, 'R')
        pdf.cell(10, 5, f"{params['aliq_icms_val']:.0f}%", 1, 0, 'C')
        pdf.cell(10, 5, f"{row.get('ALIQ_IPI', 0):.1f}%", 1, 0, 'C')
        pdf.ln()

    # --- DADOS ADICIONAIS ---
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 7)
    pdf.cell(190, 5, 'DADOS ADICIONAIS', 1, 1, 'L')
    pdf.set_font('Arial', '', 6)
    obs_fixa = f"VALOR TOTAL DOS PRODUTOS INCLUI II, PIS, COFINS E TAXAS."
    if params['is_diferido']:
        obs = f"Informacoes Complementares: ICMS DIFERIDO NO VALOR DE R$ {fmt(params['v_icms_diferido'])} CONFORME REGULAMENTO. {obs_fixa}"
    else:
        obs = f"Informacoes Complementares: OPERAÇÃO TRIBUTADA INTEGRALMENTE. {obs_fixa}"
    pdf.multi_cell(190, 4, obs, 1)
    
    return bytes(pdf.output())

# --- INTERFACE STREAMLIT (INTEGRAÇÃO TOTAL) ---
st.title("📜 ARCANUM")
st.divider()

col_cambio, col_log, col_fiscal = st.columns(3)
with col_cambio:
    taxa_cambio = st.number_input("Taxa de Câmbio", min_value=0.0, value=0.0, format="%.4f")
with col_log:
    v_frete = st.number_input("Frete Internacional", min_value=0.0, step=0.01)
    v_seguro = st.number_input("Seguro Internacional", min_value=0.0, step=0.01)
    v_taxas = st.number_input("Taxas Siscomex", min_value=0.0, step=0.01)
    v_afrmm = st.number_input("AFRMM Total", min_value=0.0, step=0.01)
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
    arquivo_subido = st.file_uploader("Suba a planilha preenchida aqui", type=["xlsx"])

# --- SEÇÃO 3: PROCESSAMENTO ---
if arquivo_subido and taxa_cambio > 0:
    df = pd.read_excel(arquivo_subido)
    df.columns = [c.upper().strip() for c in df.columns]
    
    df['VLR_UNITARIO_BRL'] = df['VLR_UNITARIO_MOEDA'] * taxa_cambio
    df['VLR_PROD_TOTAL'] = df['QTD'] * df['VLR_UNITARIO_BRL']
    total_mercadoria = df['VLR_PROD_TOTAL'].sum()
    
    # Cálculos Fiscais
    df['VLR_II_ITEM'] = df['VLR_PROD_TOTAL'] * (df.get('ALIQ_II', 0)/100)
    df['VLR_IPI_ITEM'] = (df['VLR_PROD_TOTAL'] + df['VLR_II_ITEM']) * (df.get('ALIQ_IPI', 0)/100)
    p_pis = 2.10 if regime == "Lucro Real" else 0.65
    p_cof = 9.65 if regime == "Lucro Real" else 3.00
    v_pis_total = total_mercadoria * (p_pis/100)
    v_cof_total = total_mercadoria * (p_cof/100)
    
    v_prod_composto = total_mercadoria + df['VLR_II_ITEM'].sum() + v_pis_total + v_cof_total + v_taxas
    v_ipi_tot = df['VLR_IPI_ITEM'].sum()
    base_icms_real = (v_prod_composto + v_frete + v_seguro + v_afrmm + v_ipi_tot) / (1 - (aliq_icms/100))
    v_icms_recolher = (base_icms_real * (aliq_icms/100)) * (1 - (perc_dif/100))
    v_icms_diferido = (base_icms_real * (aliq_icms/100)) * (perc_dif/100)

    # Detalhamento por Item
    df['BC_ICMS_ITEM'] = 0.00 if tem_dif == "Sim" else (df['VLR_PROD_TOTAL'] / total_mercadoria) * base_icms_real
    df['V_ICMS_ITEM'] = 0.00 if tem_dif == "Sim" else df['BC_ICMS_ITEM'] * (aliq_icms/100)

    params_pdf = {
        'v_prod_composto': v_prod_composto, 'frete': v_frete, 'seguro': v_seguro, 'afrmm': v_afrmm,
        'v_ipi_tot': v_ipi_tot, 'v_icms_diferido': v_icms_diferido,
        'aliq_icms_val': aliq_icms, 'is_diferido': (tem_dif == "Sim"),
        'cst_calculado': "051" if tem_dif == "Sim" else "100",
        'base_icms_header': 0.00 if tem_dif == "Sim" else base_icms_real,
        'v_icms_header': 0.00 if tem_dif == "Sim" else v_icms_recolher,
        'v_total_nota': v_prod_composto + v_ipi_tot + v_frete + v_seguro + v_afrmm + (0 if tem_dif == "Sim" else v_icms_recolher)
    }

    st.success("✅ Cálculos processados!")
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        buffer_xlsx = io.BytesIO()
        with pd.ExcelWriter(buffer_xlsx, engine='openpyxl') as writer: df.to_excel(writer, index=False)
        st.download_button("📥 Baixar Espelho em Excel", buffer_xlsx.getvalue(), "espelho_arcanum_conferencia.xlsx")
    with col_exp2:
        pdf_bytes = gerar_pdf(df, params_pdf)
        st.download_button("📥 Baixar PDF (Modelo 607)", pdf_bytes, "danfe_arcanum.pdf", "application/pdf")
