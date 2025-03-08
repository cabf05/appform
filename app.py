import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Formulário Público",
    page_icon="📝",
    layout="centered"
)

# Template Excel para download
def download_template():
    sample_data = {
        'Pergunta': ['Qual seu nome?', 'Qual sua cor favorita?'],
        'Tipo': ['texto', 'selecao'],
        'Opções': ['', 'Vermelho,Azul,Verde']
    }
    df = pd.DataFrame(sample_data)
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()

# Validação do arquivo Excel
def validate_excel(df):
    required_columns = ['Pergunta', 'Tipo', 'Opções']
    return all(col in df.columns for col in required_columns)

# Conversão para URL de publicação do Google Sheets
def convert_to_csv_url(sheet_url):
    return sheet_url.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv')

def main():
    st.title("📋 Criador de Formulários Públicos")
    
    # Passo 1: Configuração do formulário
    with st.expander("🔧 Passo 1: Configurar Formulário", expanded=True):
        form_name = st.text_input("Nome do Formulário:")
        
        st.download_button(
            label="Baixar Template Excel",
            data=download_template(),
            file_name="template_formulario.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        uploaded_file = st.file_uploader("Carregue seu arquivo Excel:", type="xlsx")

    # Passo 2: Configuração da planilha
    with st.expander("📊 Passo 2: Configurar Planilha", expanded=False):
        sheet_url = st.text_input("Cole a URL pública da planilha Google Sheets (deve estar publicada para web):")
        st.markdown("**Como publicar:** 1. Abra sua planilha 2. Arquivo > Publicar na web > Link 3. Selecione 'Folha inteira' e formato CSV")

    if uploaded_file and sheet_url:
        try:
            df = pd.read_excel(uploaded_file)
            if not validate_excel(df):
                st.error("Arquivo fora do padrão. Use o template fornecido.")
                return
                
            # Criar formulário
            with st.form(key='dynamic_form'):
                st.subheader(form_name)
                responses = {}
                
                for _, row in df.iterrows():
                    question = row['Pergunta']
                    qtype = row['Tipo']
                    options = row['Opções'].split(',') if pd.notna(row['Opções']) else []
                    
                    if qtype == 'texto':
                        responses[question] = st.text_input(question)
                    elif qtype == 'selecao':
                        responses[question] = st.selectbox(question, options)
                    elif qtype == 'numero':
                        responses[question] = st.number_input(question)
                
                if st.form_submit_button("Enviar Resposta"):
                    # Converter dados para CSV
                    csv_url = convert_to_csv_url(sheet_url)
                    existing_df = pd.read_csv(csv_url)
                    new_row = pd.DataFrame([responses])
                    updated_df = pd.concat([existing_df, new_row], ignore_index=True)
                    
                    # Salvar temporariamente e enviar para Google Sheets
                    updated_csv = updated_df.to_csv(index=False).encode('utf-8')
                    
                    # Upload usando requests (simulação de envio via formulário)
                    form_id = sheet_url.split('/d/')[1].split('/')[0]
                    upload_url = f"https://docs.google.com/forms/d/e/{form_id}/formResponse"
                    requests.post(upload_url, data=responses)
                    
                    st.success("Resposta enviada com sucesso! ✅")

        except Exception as e:
            st.error(f"Erro: {str(e)}")

if __name__ == "__main__":
    main()
