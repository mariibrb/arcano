import streamlit as st
import pandas as pd
import xmltodict
import io

# Configuração da Página - Mantendo a identidade visual épica
st.set_page_config(page_title="ARCANUM - Análise de Importação", layout="wide")

def carregar_estilos():
    st.markdown("""
        <style>
        .main { background-color: #0e1117; }
        .stTitle { color: #f1c40f; font-family: 'serif'; }
        </style>
    """, unsafe_allow_html=True)

def processar_xml_importacao(files):
    dados_finais = []
    
    for file in files:
        try:
            # Lógica de decifrar o XML (O Arcano em ação)
            conteudo = file.read()
            dict_xml = xmltodict.parse(conteudo)
            
            # Navegação na hierarquia fiscal do XML da NF-e de Importação
            nfe = dict_xml.get('nfeProc', {}).get('NFe', {}).get('infNFe', {})
            detalhes = nfe.get('det', [])
            
            # Garantir que detalhes seja uma lista (mesmo com um item só)
            if isinstance(detalhes, dict):
                detalhes = [detalhes]
                
            for item in detalhes:
                prod = item.get('prod', {})
                imposto = item.get('imposto', {})
                
                # Extração das 21 colunas e base de cálculo (Exemplo de lógica Arcanum)
                ii = imposto.get('II', {})
                ipi = imposto.get('IPI', {}).get('IPITrib', {})
                pis = imposto.get('PIS', {}).get('PISAliq', {})
                cofins = imposto.get('COFINS', {}).get('COFINSAliq', {})
                icms = imposto.get('ICMS', {}).get('ICMS00', {}) # Exemplo para tributada integral
                
                # Cálculo "Por Dentro" e Rateios (A essência do Arcanum)
                v_bc_ii = float(ii.get('vBC', 0))
                v_ii = float(ii.get('vII', 0))
                v_desp_adu = float(ii.get('vDespAdu', 0))
                v_iof = float(ii.get('vIOF', 0))
                
                # Memória de Cálculo do Arcano
                linha = {
                    "Item": prod.get('nItem'),
                    "NCM": prod.get('NCM'),
                    "Descrição": prod.get('xProd'),
                    "VLR_ADUANEIRO": v_bc_ii,
                    "I.I.": v_ii,
                    "I.P.I.": float(ipi.get('vIPI', 0)),
                    "PIS": float(pis.get('vPIS', 0)),
                    "COFINS": float(cofins.get('vCOFINS', 0)),
                    "TAXA_SISCOMEX": v_desp_adu,
                    "BASE_ICMS_ESTIMADA": 0.0 # Aqui entra sua fórmula complexa de Diferimento/Cálculo por dentro
                }
                
                # Cálculo do ICMS com base na alíquota interna e inter (Simulação Arcanum)
                aliq_icms = float(icms.get('pICMS', 0))
                if aliq_icms > 0:
                    # Cálculo complexo que você domina para validar o despachante
                    v_bc_icms = (v_bc_ii + v_ii + v_iof + v_desp_adu + linha["I.P.I."] + linha["PIS"] + linha["COFINS"]) / (1 - (aliq_icms/100))
                    linha["BASE_ICMS_ESTIMADA"] = round(v_bc_icms, 2)
                
                dados_finais.append(linha)
                
        except Exception as e:
            st.error(f"Erro ao decifrar o mistério do arquivo {file.name}: {e}")
            
    return pd.DataFrame(dados_finais)

# --- INTERFACE DO USUÁRIO ---
carregar_estilos()

st.title("📜 ARCANUM")
st.subheader("Decifrador de Notas Fiscais de Importação")

st.markdown("""
---
*O Arcanum analisa a hierarquia fiscal das notas de entrada, valida os cálculos do despachante 
e gera o espelho fiel para o faturamento.*
""")

uploaded_files = st.file_uploader("Envie os XMLs das Notas de Importação", type="xml", accept_multiple_files=True)

if uploaded_files:
    with st.spinner("O Arcano está processando as fórmulas..."):
        df_resultado = processar_xml_importacao(uploaded_files)
        
        if not df_resultado.empty:
            st.success("Mistérios resolvidos! Confira a análise abaixo:")
            
            # Exibição dos dados
            st.dataframe(df_resultado, use_container_width=True)
            
            # Exportação para o cliente
            csv = df_resultado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Memória de Cálculo (Espelho)",
                data=csv,
                file_name="arcanum_analise_importacao.csv",
                mime="text/csv",
            )

st.sidebar.info(f"Faz parte do Ecossistema Sentinela de Mariana.")
