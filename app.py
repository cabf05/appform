import streamlit as st
import pandas as pd
import requests
import json

# Função para ler o template Excel
def read_template(file):
    df = pd.read_excel(file, sheet_name='Form')
    return df

# Função para gerar o formulário dinâmico
def generate_form(fields):
    form_data = {}
    for _, row in fields.iterrows():
        field_name = row['Campo']
        field_type = row['Tipo']
        if field_type == 'Texto':
            form_data[field_name] = st.text_input(field_name)
        elif field_type == 'Número':
            form_data[field_name] = st.number_input(field_name, step=1)
        elif field_type == 'Data':
            form_data[field_name] = st.date_input(field_name)
    return form_data

# Função para enviar dados à planilha pública do Google Sheets
def send_to_sheets(sheet_url, data):
    sheet_id = sheet_url.split('/d/')[1].split('/')[0]
    api_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:json"
    headers = list(data.keys())
    values = list(data.values())
    
    # Obter dados existentes para determinar a próxima linha
    response = requests.get(api_url)
    if response.status_code == 200:
        json_data = json.loads(response.text.split("(", 1)[1].rsplit(")", 1)[0])
        rows = json_data.get('table', {}).get('rows', [])
        next_row = len(rows) + 1
    else:
        next_row = 1  # Se falhar, assume que é a primeira linha

    # Enviar dados usando requests para a API pública
    payload = {
        "range": f"A{next_row}",
        "majorDimension": "ROWS",
        "values": [values]
    }
    update_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/A{next_row}:append?valueInputOption=USER_ENTERED&key=AIzaSyC8WvWv1XmYQ0gGvsT2-QA4X5dL3iS6v5s"
    requests.post(update_url, json=payload)

# Interface principal
st.title("Criador de Formulários Dinâmicos")

# Passo 1: Nome do formulário
st.header("Passo 1: Nome do Formulário")
form_name = st.text_input("Digite o nome do formulário")

# Passo 2: Download do template
st.header("Passo 2: Baixe o Template Excel")
with open("template.xlsx", "rb") as file:
    st.download_button(
        label="Baixar Template",
        data=file,
        file_name="template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Passo 3: Upload do arquivo Excel
st.header("Passo 3: Faça o Upload do Arquivo Excel")
uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=["xlsx"])

# Passo 4: Link da planilha do Google Sheets
st.header("Passo 4: Link da Planilha Pública")
sheet_url = st.text_input("Cole o link da planilha pública do Google Sheets")

# Processamento e geração do formulário
if form_name and uploaded_file and sheet_url:
    try:
        fields = read_template(uploaded_file)
        st.subheader(f"Formulário: {form_name}")
        form_data = generate_form(fields)
        
        if st.button("Enviar Respostas"):
            send_to_sheets(sheet_url, form_data)
            st.success("Respostas enviadas com sucesso!")
    except Exception as e:
        st.error(f"Erro ao processar o formulário: {e}")
else:
    st.info("Por favor, preencha todos os campos para continuar.")
