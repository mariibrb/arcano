import streamlit as st
import pandas as pd
import io
from fpdf import FPDF

# Configuração Básica - Design Nativo e Amplo
st.set_page_config(page_title="ARCANUM - Auditoria de Importação", layout="wide")

# --- CLASSE PARA GERAÇÃO DO PDF (LAYOUT FIEL AO MODELO ENVIADO) ---
class EspelhoDANFE(FPDF):
    def header(self):
        # Cabeçalho principal conforme o padrão DANFE
        self.set_font('Arial', 'B', 14)
        self.cell(130, 15, 'Espelho de Nota Fiscal (IMPORTAÇÃO)', 1, 0, 'C')
        
        self.set_font('Arial', '', 8)
        # Quadro Identificação da Nota
        curr_y = self.get_y()
        curr_x = self.get_x()
        self.rect(curr_x, curr_y, 60, 15)
        self.set_xy(curr_x, curr_y + 2)
        self.cell(60, 4, 'Número: 000524', 0, 1, 'C')
        self.cell(130, 4, '', 0, 0) # offset
        self.cell(60, 4, 'Série: 1', 0, 1, 'C')
        self.cell(130, 4, '', 0, 0) # offset
        self.cell(60, 4, 'Entrada [X] Saída [ ]', 0, 1, 'C')
        
        self.set_xy(10, curr_y + 15)
        
        # Dados do Destinatário/Remetente
        self.set_font('Arial', 'B', 8)
        self.set_fill_color(240, 240, 240)
        self.cell(190, 8, 'DESTINATÁRIO / REMETENTE (EXPORTADOR ESTRANGEIRO)', 1, 1, 'L', fill=True)
        
        self.set_font('Arial', '', 7)
        # Linha 1 Nome e Emissão
        self.cell(130, 8, 'Nome/Razão Social: ZHEJIANG SANZHENG LUGGAGE', 1, 0, 'L')
        self.cell(60, 8, 'Data Emissão: 30/01/2026', 1, 1, 'L')
        
        # Linha 2 Endereço e UF
        self.cell(130, 8, 'Endereço: ROOM 101, BUILDING 2, AREA 10A, JINHUA, ZHEJIANG', 1, 0, 'L')
        self.cell(60, 8, 'UF: EX', 1, 1, 'L')
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_pdf(df_final, params):
    pdf = EspelhoDANFE()
    pdf.add_page()
    
    # --- QUADRO: CÁLCULO DOS IMPOSTOS ---
    pdf.set_font('Arial', 'B', 8)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 7, 'CÁLCULO DOS IMPOSTOS', 1, 1, 'L', fill=True)
    
    # Função auxiliar para formatar padrão brasileiro
    fmt = lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Estilo de célula para títulos menores dentro dos quadros
    def cell_label(w, h, txt, val, border=1, ln=0):
        curr_x = pdf.get_x()
        curr_y = pdf.get_y()
        pdf.rect(curr_x, curr_y, w, h)
        pdf.set_font('Arial', '', 6)
        pdf.cell(w, h/2, txt, 0, 1, 'L')
        pdf.set_x(curr_x)
        pdf.set_font('Arial', 'B', 7)
        pdf.cell(w, h/2, val, 0, 0, 'R')
        pdf.set_xy(curr_x + w, curr_y)
        if ln == 1: pdf.ln(h)

    # Linha 1 de impostos
    cell_label(38, 10, "BASE DE CÁLC. ICMS", fmt(params['base_icms_tot']))
    cell_label(38, 10, "VALOR DO ICMS", fmt(params['base_icms_tot'] * 0.18 - params['icms_diferido_tot']))
    cell_label(38, 10, "BASE CÁLC. ICMS ST", "0,00")
    cell_label(38, 10, "VALOR DO ICMS ST", "0,00")
    cell_label(38, 10, "V. TOTAL PRODUTOS", fmt(params['v_prod_danfe']), ln=1)
    
    # Linha 2 de impostos
    cell_label(38, 10, "VALOR DO FRETE", fmt(params['frete']))
    cell_label(38, 10, "VALOR DO SEGURO", fmt(params['seguro']))
    cell_label(38, 10, "DESCONTO", "0,00")
    cell_label(38, 10, "OUTRAS DESP. ACESS.", fmt(params['desp_assessorias']))
    cell_label(38, 10, "VALOR DO IPI", fmt(params['v_ipi_tot']), ln=1)

    # Valor Total da Nota em destaque
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(152, 10, "VALOR TOTAL DA NOTA", 1, 0, 'R', fill=True)
    pdf.cell(38, 10, f"R$ {fmt(params['v_total_nota'])}", 1, 1, 'R', fill=True)
    
    # Informações Complementares
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 7)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 5, "DADOS ADICIONAIS / INFORMAÇÕES COMPLEMENTARES", 1, 1, 'L', fill=True)
    pdf.set_font('Arial', '', 6)
    
    obs = (f"D.I.: 2601704700 | Data: 28/01/2026 | CIF: {fmt(params['cif'])} | "
           f"PIS: {fmt(params['pis_tot'])} | COFINS: {fmt(params['cofins_tot'])} | "
           f"Taxa Siscomex: {fmt(params['taxa_sis'])} | AFRMM: {fmt(params['afrmm'])}\n"
           f"ICMS DIFERIDO NO VALOR DE R$ {fmt(params['icms_diferido_tot'])} CONFORME REGULAMENTO.")
    pdf.multi_cell(190, 4, obs, 1)
    pdf.ln(4)

    # --- TABELA DE PRODUTOS ---
    pdf.set_font('Arial', 'B', 7)
    pdf.set_fill_color(230, 230, 230)
    # Cabeçalho da Tabela
    cols_pdf = [('CÓDIGO', 15), ('DESCRIÇÃO DOS PRODUTOS', 70), ('NCM', 18), ('CST', 10), ('CFOP', 10), ('QTD', 12), ('V. UNIT', 18), ('V. TOTAL', 18), ('%IPI', 9)]
    
    for col_name, width in cols_pdf:
        pdf.cell(width, 7, col_name, 1, 0, 'C', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 6)
    for index, row in df_final.iterrows():
        pdf.cell(15, 6, "021", 1, 0, 'C')
        pdf.cell(70, 6, str(row.get('PRODUTO', ''))[:45], 1)
        pdf.cell(18, 6, str(row.get('NCM', '')), 1, 0, 'C')
        pdf.cell(10, 6, "000", 1, 0, 'C')
        pdf.cell(10, 6, "3102", 1, 0, 'C')
        pdf.cell(12, 6, f"{row.get('QTD', 0):.0f}", 1, 0, 'C')
        pdf.cell(18, 6, fmt(row.get('VLR_UNITARIO_BRL', 0)), 1, 0, 'R')
        pdf.cell(18, 6, fmt(row.get('VLR_PROD_TOTAL', 0)), 1, 0, 'R')
        pdf.cell(9, 6, "0,00", 1, 0, 'C')
        pdf.ln()
        
    return bytes(pdf.output())

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
    p_pis_aliq = 2.10 if "Real" in regime else 0.65
    p_cofins_aliq = 9.65 if "Real" in regime else 3.00
    if st.checkbox("Aplicar Majorada (+1% COFINS)"):
        p_cofins_aliq += 1.0
    aliq_icms = st.number_input("Alíquota ICMS (%)", value=18.0, step=0.1)
    with st.expander("Configurar Diferimento"):
        tem_dif = st.radio("Haverá Diferimento?", ("Não", "Sim"), horizontal=True)
        perc_dif = 0.0
        if tem_dif == "Sim":
            perc_dif = st.number_input("Percentual Diferido (0-100%)", value=100.0, step=0.1)

st.divider()

# --- SEÇÃO 2: MODELO E UPLOAD ---
st.subheader("📋 2. Itens da Importação")
arquivo_subido = st.file_uploader("Suba a planilha preenchida aqui", type=["xlsx"])

# --- SEÇÃO 3: CÁLCULOS E RESULTADOS ---
if arquivo_subido:
    df = pd.read_excel(arquivo_subido)
    with st.spinner("Processando auditoria fiscal..."):
        df.columns = [c.upper().strip() for c in df.columns]
        col_vlr = next((c for c in ['VLR_UNITARIO_MOEDA', 'VLR_UNITARIO', 'VALOR_UNITARIO', 'VALOR'] if c in df.columns), None)
        col_qtd = next((c for c in ['QTD', 'QUANTIDADE'] if c in df.columns), None)

        if col_vlr is None or col_qtd is None:
            st.error(f"❌ Erro de Colunas: Verifique a planilha.")
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
            df['VLR_PIS'] = df['VLR_ADUANEIRO'] * (p_pis_aliq / 100)
            df['VLR_COFINS'] = df['VLR_ADUANEIRO'] * (p_cofins_aliq / 100)
            
            soma_componentes = (df['VLR_ADUANEIRO'] + df['VLR_II'] + df['VLR_IPI'] + 
                                df['VLR_PIS'] + df['VLR_COFINS'] + df['RAT_TAXAS'] + df['RAT_AFRMM'])
            df['BASE_ICMS'] = soma_componentes / (1 - (aliq_icms / 100))
            df['ICMS_CHEIO'] = df['BASE_ICMS'] * (aliq_icms / 100)
            df['VLR_DIFERIDO'] = df['ICMS_CHEIO'] * (perc_dif / 100)
            df['ICMS_RECOLHER'] = df['ICMS_CHEIO'] - df['VLR_DIFERIDO']
            
            st.divider()
            st.success("📝 Espelho Gerado!")
            col_exibicao = ['DI', 'ADICAO', 'ITEM', 'NCM', 'PRODUTO', 'VLR_ADUANEIRO', 'VLR_II', 'RAT_AFRMM', 'BASE_ICMS', 'ICMS_RECOLHER']
            cols_reais = [c for c in col_exibicao if c in df.columns]
            st.dataframe(df[cols_reais].style.format(precision=2), use_container_width=True)

            # PARÂMETROS PARA O PDF SEGUINDO O MODELO
            v_prod_danfe = df['VLR_ADUANEIRO'].sum() + df['VLR_II'].sum()
            v_desp_assessorias = df['VLR_PIS'].sum() + df['VLR_COFINS'].sum() + v_taxas
            
            params_pdf = {
                'base_icms_tot': df['BASE_ICMS'].sum(),
                'v_ipi_tot': df['VLR_IPI'].sum(),
                'v_prod_danfe': v_prod_danfe,
                'frete': v_frete,
                'seguro': v_seguro,
                'desp_assessorias': v_desp_assessorias,
                'afrmm': v_afrmm,
                'v_total_nota': v_prod_danfe + df['VLR_IPI'].sum() + v_desp_assessorias + v_afrmm + df['ICMS_RECOLHER'].sum(),
                'icms_diferido_tot': df['VLR_DIFERIDO'].sum(),
                'pis_tot': df['VLR_PIS'].sum(),
                'cofins_tot': df['VLR_COFINS'].sum(),
                'taxa_sis': v_taxas,
                'cif': df['VLR_ADUANEIRO'].sum()
            }

            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                buffer_xlsx = io.BytesIO()
                with pd.ExcelWriter(buffer_xlsx, engine='openpyxl') as writer: df.to_excel(writer, index=False)
                st.download_button("📥 Baixar Espelho em Excel", buffer_xlsx.getvalue(), "espelho_arcanum_conferencia.xlsx")
            with col_exp2:
                pdf_bytes_data = gerar_pdf(df, params_pdf)
                st.download_button("📥 Baixar PDF (Modelo Espelho)", pdf_bytes_data, "espelho_arcanum_danfe.pdf", "application/pdf")
