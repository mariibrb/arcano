import streamlit as st
import pandas as pd
import io
from fpdf import FPDF

# Configuração Básica - Design Nativo e Amplo
st.set_page_config(page_title="ARCANUM - Auditoria de Importação", layout="wide")

# --- CLASSE PARA GERAÇÃO DO PDF (LAYOUT FIEL AO MODELO ENVIADO) ---
class EspelhoDANFE(FPDF):
    def header(self):
        # Cabeçalho principal
        self.set_font('Arial', 'B', 14)
        self.cell(130, 15, 'Espelho de Nota Fiscal', 1, 0, 'C')
        self.set_font('Arial', '', 8)
        self.cell(60, 15, 'Entrada [X] Saída [ ]', 1, 1, 'C')
        
        # Dados do Destinatário (Baseado no seu modelo)
        self.set_font('Arial', 'B', 8)
        self.set_fill_color(240, 240, 240)
        self.cell(190, 8, 'DESTINATÁRIO / REMETENTE', 1, 1, 'L', fill=True)
        self.set_font('Arial', '', 8)
        self.cell(190, 8, 'Nome/Razão Social: ZHEJIANG SANZHENG LUGGAGE', 1, 1, 'L')
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_pdf(df_final, params):
    pdf = EspelhoDANFE()
    pdf.add_page()
    
    # --- DADOS DA DI (DADOS ADICIONAIS) ---
    pdf.set_font('Arial', 'B', 8)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 8, 'DADOS ADICIONAIS / IMPOSTOS GLOBAIS', 1, 1, 'L', fill=True)
    pdf.set_font('Arial', '', 8)
    pdf.cell(63, 8, f"Nr. DI: {params['di_num']}", 1, 0)
    pdf.cell(63, 8, f"Data DI: {params['di_data']}", 1, 0)
    pdf.cell(64, 8, f"AFRMM: {params['afrmm']:.2f}", 1, 1)
    
    pdf.cell(63, 8, f"PIS: {params['pis_tot']:.2f}", 1, 0)
    pdf.cell(63, 8, f"Cofins: {params['cofins_tot']:.2f}", 1, 0)
    pdf.cell(64, 8, f"Taxa Siscomex: {params['taxa_sis']:.2f}", 1, 1)
    pdf.ln(5)

    # --- TABELA DE PRODUTOS ---
    pdf.set_font('Arial', 'B', 7)
    pdf.set_fill_color(230, 230, 230)
    # Colunas conforme o seu PDF: Cod, Descrição, NCM, Qtd, Vl Unit, Vl Tot, ICMS, IPI
    cols = ['Cod', 'Descricao', 'NCM', 'Qtd', 'Vl Unit', 'Vl Tot', 'ICMS%', 'IPI%', 'ICMS Rec']
    widths = [10, 55, 20, 15, 20, 20, 15, 15, 20]
    
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 7, col, 1, 0, 'C', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 6)
    for index, row in df_final.iterrows():
        pdf.cell(widths[0], 6, str(row.get('ITEM', index+1)), 1, 0, 'C')
        pdf.cell(widths[1], 6, str(row.get('PRODUTO', ''))[:40], 1)
        pdf.cell(widths[2], 6, str(row.get('NCM', '')), 1, 0, 'C')
        pdf.cell(widths[3], 6, str(row.get('QTD', 0)), 1, 0, 'C')
        pdf.cell(widths[4], 6, f"{row.get('VLR_UNITARIO_BRL', 0):.2f}", 1, 0, 'R')
        pdf.cell(widths[5], 6, f"{row.get('VLR_PROD_TOTAL', 0):.2f}", 1, 0, 'R')
        pdf.cell(widths[6], 6, f"{params['aliq_icms']:.2f}", 1, 0, 'C')
        pdf.cell(widths[7], 6, f"{row.get('ALIQ_IPI', 0):.2f}", 1, 0, 'C')
        pdf.cell(widths[8], 6, f"{row.get('ICMS_RECOLHER', 0):.2f}", 1, 0, 'R')
        pdf.ln()
        
    return pdf.output()

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
    di_num = st.text_input("Número da DI", "2601704700")
    di_data = st.text_input("Data da DI", "28/01/2026")

with col_log:
    st.subheader("🚛 Logística e Taxas (R$)")
    v_frete = st.number_input("Frete Internacional Total", min_value=0.0, step=0.01, format="%.2f")
    v_seguro = st.number_input("Seguro Internacional Total", min_value=0.0, step=0.01, format="%.2f")
    v_taxas = st.number_input("Taxa Siscomex / Outras Taxas", min_value=0.0, step=0.01, format="%.2f")
    v_afrmm = st.number_input("Valor Total AFRMM (Marítimo)", min_value=0.0, step=0.01, format="%.2f")

with col_fiscal:
    st.subheader("⚖️ Fiscal e ICMS")
    regime = st.selectbox("Regime PIS/COFINS", ["Lucro Real (11,75%)", "Lucro Presumido (3,65%)"])
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
        'DI': ['26/0000001-0'], 'ADICAO': ['001'], 'ITEM': [1], 'NCM': ['42021210'],
        'PRODUTO': ['MALAS DE BORDO REVESTIDAS'], 'QTD': [495], 'VLR_UNITARIO_MOEDA': [257.83], 'ALIQ_II': [14.0], 'ALIQ_IPI': [6.5]
    })
    buffer_mod = io.BytesIO()
    with pd.ExcelWriter(buffer_mod, engine='openpyxl') as writer:
        df_modelo.to_excel(writer, index=False)
    st.download_button(label="📥 Baixar Planilha Modelo", data=buffer_mod.getvalue(), file_name="modelo_arcanum_di.xlsx")

with col_up:
    arquivo_subido = st.file_uploader("Suba a planilha preenchida aqui", type=["xlsx"])

# --- SEÇÃO 3: CÁLCULOS E RESULTADOS ---
if arquivo_subido:
    df = pd.read_excel(arquivo_subido)
    with st.spinner("Processando auditoria fiscal..."):
        df.columns = [c.upper().strip() for c in df.columns]
        col_vlr = next((c for c in ['VLR_UNITARIO_MOEDA', 'VLR_UNITARIO', 'VALOR_UNITARIO', 'VALOR'] if c in df.columns), None)
        col_qtd = next((c for c in ['QTD', 'QUANTIDADE'] if c in df.columns), None)

        if col_vlr is None or col_qtd is None:
            st.error(f"❌ Erro de Colunas: Certifique-se que a planilha tem as colunas 'QTD' e 'VLR_UNITARIO_MOEDA'.")
            st.stop()

        df['VLR_UNITARIO_BRL'] = df[col_vlr] * taxa_cambio
        df['VLR_PROD_TOTAL'] = df[col_qtd] * df['VLR_UNITARIO_BRL']
        total_geral_prods = df['VLR_PROD_TOTAL'].sum()
        
        if total_geral_prods > 0:
            df['RAT_FRETE'] = (df['VLR_PROD_TOTAL'] / total_geral_prods) * v_frete
            df['RAT_SEGURO'] = (df['VLR_PROD_TOTAL'] / total_geral_prods) * v_seguro
            df['RAT_TAXAS'] = (df['VLR_PROD_TOTAL'] / total_geral_prods) * v_taxas
            df['RAT_AFRMM'] = (df['VLR_PROD_TOTAL'] / total_geral_prods) * v_afrmm
            df['VLR_ADUANEIRO'] = df['VLR_PROD_TOTAL'] + df['RAT_FRETE'] + df['RAT_SEGURO']
            df['VLR_II'] = df['VLR_ADUANEIRO'] * (df.get('ALIQ_II', 0) / 100)
            df['VLR_IPI'] = (df['VLR_ADUANEIRO'] + df['VLR_II']) * (df.get('ALIQ_IPI', 0) / 100)
            df['VLR_PIS'] = df['VLR_ADUANEIRO'] * (p_pis / 100)
            df['VLR_COFINS'] = df['VLR_ADUANEIRO'] * (p_cofins / 100)
            
            soma_componentes = (df['VLR_ADUANEIRO'] + df['VLR_II'] + df['VLR_IPI'] + 
                                df['VLR_PIS'] + df['VLR_COFINS'] + df['RAT_TAXAS'] + df['RAT_AFRMM'])
            df['BASE_ICMS'] = soma_componentes / (1 - (aliq_icms / 100))
            df['ICMS_CHEIO'] = df['BASE_ICMS'] * (aliq_icms / 100)
            df['VLR_DIFERIDO'] = df['ICMS_CHEIO'] * (perc_dif / 100)
            df['ICMS_RECOLHER'] = df['ICMS_CHEIO'] - df['VLR_DIFERIDO']
            
            st.divider()
            st.success("📝 Espelho da Nota Fiscal Gerado!")
            cols_exibicao = ['DI', 'ADICAO', 'ITEM', 'NCM', 'PRODUTO', 'VLR_ADUANEIRO', 'VLR_II', 'RAT_AFRMM', 'BASE_ICMS', 'ICMS_RECOLHER']
            st.dataframe(df[cols_exibicao].style.format(precision=2), use_container_width=True)

            # Parâmetros para o PDF
            params_pdf = {
                'di_num': di_num, 'di_data': di_data, 'afrmm': v_afrmm,
                'pis_tot': df['VLR_PIS'].sum(), 'cofins_tot': df['VLR_COFINS'].sum(),
                'taxa_sis': v_taxas, 'aliq_icms': aliq_icms
            }

            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                buffer_xlsx = io.BytesIO()
                with pd.ExcelWriter(buffer_xlsx, engine='openpyxl') as writer: df.to_excel(writer, index=False)
                st.download_button("📥 Baixar Espelho em Excel", buffer_xlsx.getvalue(), "espelho_arcanum.xlsx")
            with col_exp2:
                pdf_output = gerar_pdf(df, params_pdf)
                st.download_button("📥 Baixar PDF (Estilo DANFE)", pdf_output, "espelho_danfe_arcanum.pdf", "application/pdf")
        else:
            st.error("Erro: O Valor Bruto resultou em zero.")
