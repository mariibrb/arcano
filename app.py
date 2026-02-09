import streamlit as st
import pandas as pd
import io
from fpdf import FPDF

# Configuração Básica
st.set_page_config(page_title="ARCANUM - Auditoria", layout="wide")

# --- CLASSE PARA GERAÇÃO DO PDF (LAYOUT FIEL AO DOCUMENTO) ---
class EspelhoDANFE(FPDF):
    def header(self):
        # Topo estilo Nota Fiscal
        self.set_font('Arial', 'B', 14)
        self.cell(130, 15, 'Espelho de Nota Fiscal', 1, 0, 'C')
        self.set_font('Arial', '', 8)
        self.cell(60, 15, 'Entrada [X] Saída [ ]', 1, 1, 'C')
        
        # Dados da DI e Documento (Exemplo baseado no seu PDF)
        self.set_font('Arial', 'B', 8)
        self.cell(190, 8, 'DESTINATÁRIO / REMETENTE', 1, 1, 'L', fill=True)
        self.set_font('Arial', '', 8)
        self.cell(190, 8, 'Razão Social: ZHEJIANG SANZHENG LUGGAGE', 1, 1, 'L')
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} - Gerado por ARCANUM', 0, 0, 'C')

def gerar_pdf_danfe(df_final, params):
    pdf = EspelhoDANFE()
    pdf.add_page()
    
    # --- DADOS ADICIONAIS DA DI ---
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(190, 8, 'DADOS ADICIONAIS DA IMPORTAÇÃO', 1, 1, 'L', fill=True)
    pdf.set_font('Arial', '', 8)
    pdf.cell(95, 8, f"Nr. DI: {params['di_num']}", 1, 0)
    pdf.cell(95, 8, f"Data DI: {params['di_data']}", 1, 1)
    pdf.cell(63, 8, f"PIS: {params['v_pis_tot']:.2f}", 1, 0)
    pdf.cell(63, 8, f"COFINS: {params['v_cofins_tot']:.2f}", 1, 0)
    pdf.cell(64, 8, f"AFRMM: {params['v_afrmm']:.2f}", 1, 1)
    pdf.ln(2)

    # --- TABELA DE PRODUTOS ---
    pdf.set_font('Arial', 'B', 7)
    pdf.set_fill_color(220, 220, 220)
    # Cabeçalho da tabela igual ao seu PDF
    cols = ['Cod', 'Descrição', 'NCM', 'Qtd', 'Vl Unit', 'Vl Tot', 'II', 'IPI', 'ICMS']
    w = [10, 60, 20, 15, 20, 20, 15, 15, 15]
    
    for i, col in enumerate(cols):
        pdf.cell(w[i], 7, col, 1, 0, 'C', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 6)
    for _, row in df_final.iterrows():
        # Truncar descrição longa para não quebrar o PDF
        desc = str(row.get('PRODUTO', ''))[:45]
        pdf.cell(w[0], 6, str(row.get('ITEM', '')), 1, 0, 'C')
        pdf.cell(w[1], 6, desc, 1)
        pdf.cell(w[2], 6, str(row.get('NCM', '')), 1, 0, 'C')
        pdf.cell(w[3], 6, str(row.get('QTD', '')), 1, 0, 'C')
        pdf.cell(w[4], 6, f"{row.get('VLR_UNITARIO_BRL', 0):.2f}", 1, 0, 'R')
        pdf.cell(w[5], 6, f"{row.get('VLR_PROD_TOTAL', 0):.2f}", 1, 0, 'R')
        pdf.cell(w[6], 6, f"{row.get('VLR_II', 0):.2f}", 1, 0, 'R')
        pdf.cell(w[7], 6, f"{row.get('VLR_IPI', 0):.2f}", 1, 0, 'R')
        pdf.cell(w[8], 6, f"{row.get('ICMS_RECOLHER', 0):.2f}", 1, 0, 'R')
        pdf.ln()

    return pdf.output()

# --- INTERFACE ---
st.title("📜 ARCANUM")
st.write("Projeto Sentinela - Auditoria Fiscal de Importação")
st.divider()

# Parâmetros em colunas na página principal (Espaço Amplo)
st.header("⚙️ 1. Configurações da DI")
c1, c2, c3 = st.columns(3)

with c1:
    di_num = st.text_input("Número da DI", value="2601704700")
    di_data = st.text_input("Data da DI", value="28/01/2026")
    taxa_cambio = st.number_input("Taxa de Câmbio (USD/BRL)", value=5.0000, format="%.4f")

with c2:
    v_frete = st.number_input("Frete Total (R$)", value=0.0, step=0.01)
    v_seguro = st.number_input("Seguro Total (R$)", value=0.0, step=0.01)
    v_siscomex = st.number_input("Taxa Siscomex (R$)", value=0.0, step=0.01)
    v_afrmm = st.number_input("AFRMM (R$)", value=0.0, step=0.01)

with c3:
    regime = st.selectbox("Regime", ["Lucro Real (11,75%)", "Lucro Presumido (3,65%)"])
    aliq_icms = st.number_input("ICMS (%)", value=18.0)
    perc_dif = st.number_input("% Diferimento", value=0.0)

st.divider()

# Upload
st.subheader("📋 2. Upload de Itens")
arquivo = st.file_uploader("Suba a planilha de itens", type=["xlsx"])

if arquivo:
    df = pd.read_excel(arquivo)
    with st.spinner("Processando..."):
        df.columns = [c.upper().strip() for c in df.columns]
        
        # Identificação de colunas para evitar KeyError
        col_vlr = next((c for c in ['VLR_UNITARIO_MOEDA', 'VLR_UNITARIO'] if c in df.columns), None)
        col_qtd = next((c for c in ['QTD', 'QUANTIDADE'] if c in df.columns), None)

        if not col_vlr or not col_qtd:
            st.error("Colunas essenciais não encontradas (QTD/VLR_UNITARIO_MOEDA)!")
            st.stop()

        # Cálculos de Base
        df['VLR_UNITARIO_BRL'] = df[col_vlr] * taxa_cambio
        df['VLR_PROD_TOTAL'] = df[col_qtd] * df['VLR_UNITARIO_BRL']
        total_di_brl = df['VLR_PROD_TOTAL'].sum()
        
        # Rateios
        df['RAT_FRETE'] = (df['VLR_PROD_TOTAL'] / total_di_brl) * v_frete
        df['RAT_SEGURO'] = (df['VLR_PROD_TOTAL'] / total_di_brl) * v_seguro
        df['RAT_SISCOMEX'] = (df['VLR_PROD_TOTAL'] / total_di_brl) * v_siscomex
        df['RAT_AFRMM'] = (df['VLR_PROD_TOTAL'] / total_di_brl) * v_afrmm
        
        # Valor Aduaneiro e Impostos
        df['VLR_ADUANEIRO'] = df['VLR_PROD_TOTAL'] + df['RAT_FRETE'] + df['RAT_SEGURO']
        df['VLR_II'] = df['VLR_ADUANEIRO'] * (df.get('ALIQ_II', 0) / 100)
        df['VLR_IPI'] = (df['VLR_ADUANEIRO'] + df['VLR_II']) * (df.get('ALIQ_IPI', 0) / 100)
        
        p_pis = 2.10 if "Real" in regime else 0.65
        p_cofins = 9.65 if "Real" in regime else 3.00
        df['VLR_PIS'] = df['VLR_ADUANEIRO'] * (p_pis / 100)
        df['VLR_COFINS'] = df['VLR_ADUANEIRO'] * (p_cofins / 100)
        
        # Base ICMS Por Dentro
        soma_base = (df['VLR_ADUANEIRO'] + df['VLR_II'] + df['VLR_IPI'] + 
                     df['VLR_PIS'] + df['VLR_COFINS'] + df['RAT_SISCOMEX'] + df['RAT_AFRMM'])
        df['BASE_ICMS'] = soma_base / (1 - (aliq_icms / 100))
        df['ICMS_RECOLHER'] = (df['BASE_ICMS'] * (aliq_icms / 100)) * (1 - (perc_dif / 100))

        st.success("✅ Cálculos Finalizados")
        
        # Exibição segura na tela
        cols_mostrar = ['ADICAO', 'NCM', 'PRODUTO', 'VLR_ADUANEIRO', 'VLR_II', 'BASE_ICMS', 'ICMS_RECOLHER']
        cols_existentes = [c for c in cols_mostrar if c in df.columns]
        st.dataframe(df[cols_existentes].style.format(precision=2), use_container_width=True)

        # Exportações
        params_pdf = {
            'di_num': di_num, 'di_data': di_data, 'v_afrmm': v_afrmm,
            'v_pis_tot': df['VLR_PIS'].sum(), 'v_cofins_tot': df['VLR_COFINS'].sum()
        }
        
        c_xls, c_pdf = st.columns(2)
        with c_xls:
            buf_xls = io.BytesIO()
            with pd.ExcelWriter(buf_xls, engine='openpyxl') as wr: df.to_excel(wr, index=False)
            st.download_button("📥 Baixar Excel Completo", buf_xls.getvalue(), "resultado_arcanum.xlsx")
        
        with c_pdf:
            pdf_bytes = gerar_pdf_danfe(df, params_pdf)
            st.download_button("📥 Baixar PDF (Espelho NF)", bytes(pdf_bytes), "espelho_danfe.pdf", "application/pdf")
