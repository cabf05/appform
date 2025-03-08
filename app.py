import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import csv

# Configurações da página
st.set_page_config(page_title="Formulário Público", page_icon="📝", layout="centered")

def download_template():
    sample_data = {
        'Pergunta': ['Qual seu nome?', 'Qual sua idade?'],
        'Tipo': ['texto', 'numero'],
        'Opções': ['', '']
    }
    df = pd.DataFrame(sample_data)
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()

def validate_excel(df):
    required_columns = ['Pergunta', 'Tipo', 'Opções']
    return all(col in df.columns for col in required_columns)

def convert_sheet_url(url):
    """Converte URL de edição para URL de exportação CSV"""
    if '/edit#' in url:
        return url.replace('/edit#', '/export?format=csv&gid=')
    return f"{url.split('?')[0]}/export?format=csv"

def main():
    st.title("📋 Formulário Público Simplificado")
    
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
        sheet_url = st.text_input("Cole a URL pública da planilha Google Sheets:")
        st.markdown("""
            **Configuração necessária:**
            1. Compartilhe a planilha como 'Qualquer pessoa com o link pode editar'
            2. Formato deve ser: https://docs.google.com/spreadsheets/d/SEU_ID/edit
        """)

    if uploaded_file and sheet_url:
        try:
            df = pd.read_excel(uploaded_file)
            if not validate_excel(df):
                st.error("Formato do arquivo inválido. Use o template fornecido.")
                return
                
            # Criar formulário
            with st.form(key='dynamic_form'):
                st.subheader(form_name)
                responses = {}
                
                for _, row in df.iterrows():
                    question = row['Pergunta']
                    qtype = row['Tipo'].lower()
                    options = row['Opções'].split(',') if pd.notna(row['Opções']) else []
                    
                    if qtype == 'texto':
                        responses[question] = st.text_input(question)
                    elif qtype == 'selecao':
                        responses[question] = st.selectbox(question, options)
                    elif qtype == 'numero':
                        responses[question] = st.number_input(question)
                
                if st.form_submit_button("Enviar Resposta"):
                    # Converter dados para formato de URL
                    csv_url = convert_sheet_url(sheet_url)
                    
                    # Preparar dados para envio
                    form_data = {
                        'submit': 'Enviar',
                        'action': sheet_url.split('/d/')[1].split('/')[0]
                    }
                    form_data.update({k: v for k, v in responses.items() if v})
                    
                    # Enviar dados via POST
                    response = requests.post(
                        'https://docs.google.com/forms/d/e/your-form-id/formResponse',
                        data=form_data
                    )
                    
                    if response.status_code == 200:
                        st.success("Resposta enviada com sucesso! ✅")
                    else:
                        st.error("Erro ao enviar resposta. Verifique a URL da planilha.")

        except Exception as e:
            st.error(f"Erro: {str(e)}")

if __name__ == "__main__":
    main()
