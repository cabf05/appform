import streamlit as st
import pandas as pd
import requests
import json
import openpyxl
from io import BytesIO

# Função para gerar o template Excel dinamicamente
def generate_template():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Form"
    ws.append(["Campo", "Tipo"])
    # Adiciona linhas de exemplo
    ws.append(["Nome", "Texto"])
    ws.append(["Idade", "Número"])
    ws.append(["Data de Nascimento", "Data"])
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

# Função para ler o arquivo Excel enviado pelo usuário
def read_template(file):
    df = pd.read_excel(file, sheet_name="Form")
    return df

# Função para gerar o formulário dinâmico
def generate_form(fields):
    form_data = {}
    for _, row in fields.iterrows():
        field_name = row["Campo"]
        field_type = row["Tipo"]
        if field_type == "Texto":
            form_data[field_name] = st.text_input(field_name)
        elif field_type == "Número":
            form_data[field_name] = st.number_input(field_name, step=1)
        elif field_type == "Data":
            form_data[field_name] = st.date_input(field_name)
    return form_data

# Função para enviar dados para o Google Sheets com tratamento de erros
def send_to_sheets(sheet_url, data):
    try:
        # Extrair o ID da planilha
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        st.write(f"ID da planilha: {sheet_id}")  # Mostra o ID

        # Verificar quantas linhas já existem
        api_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:json"
        response = requests.get(api_url)
        if response.status_code != 200:
            st.error(f"Erro ao acessar a planilha: {response.text}")
            return

        # Calcular a próxima linha
        json_data = json.loads(response.text.split("(", 1)[1].rsplit(")", 1)[0])
        rows = json_data.get("table", {}).get("rows", [])
        next_row = len(rows) + 1
        st.write(f"Próxima linha: {next_row}")  # Mostra a linha

        # Preparar os dados
        values = list(data.values())
        st.write(f"Dados enviados: {values}")  # Mostra os dados

        # Enviar para a planilha
        update_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/A{next_row}:append?valueInputOption=USER_ENTERED&key=SUA_CHAVE_API"
        payload = {"range": f"A{next_row}", "majorDimension": "ROWS", "values": [values]}
        response = requests.post(update_url, json=payload)

        # Verificar o resultado
        if response.status_code == 200:
            st.success("Respostas enviadas com sucesso!")
        else:
            st.error(f"Erro ao enviar: {response.text}")
    except Exception as e:
        st.error(f"Erro no processo: {e}")

# Interface principal
st.title("Criador de Formulários Dinâmicos")

# Passo 1: Nome do formulário
st.header("Passo 1: Nome do Formulário")
form_name = st.text_input("Digite o nome do formulário")

# Passo 2: Download do template gerado dinamicamente
st.header("Passo 2: Baixe o Template Excel")
template_buffer = generate_template()
st.download_button(
    label="Baixar Template",
    data=template_buffer,
    file_name="template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Passo 3: Upload do arquivo Excel preenchido
st.header("Passo 3: Faça o Upload do Arquivo Excel")
uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=["xlsx"])

# Passo 4: Link do Google Sheets
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
    except Exception as e:
        st.error(f"Erro ao processar o formulário: {e}")
else:
    st.info("Por favor, preencha todos os campos para continuar.")
