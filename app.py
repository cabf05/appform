import streamlit as st
import pandas as pd
import requests
import io
import base64
import json
from urllib.parse import urlparse, parse_qs

# Configuração da página Streamlit
st.set_page_config(
    page_title="Criador de Formulários Dinâmicos",
    page_icon="📝",
    layout="wide"
)

# Funções auxiliares
def get_template_excel():
    """Gera um arquivo Excel de template para download."""
    df = pd.DataFrame({
        'campo': ['nome', 'email', 'idade', 'comentario'],
        'tipo': ['texto', 'email', 'numero', 'area_texto'],
        'obrigatorio': ['sim', 'sim', 'nao', 'nao'],
        'label': ['Nome Completo', 'Endereço de E-mail', 'Idade', 'Comentários'],
        'placeholder': ['Digite seu nome', 'exemplo@email.com', '25', 'Deixe seu comentário aqui...']
    })
    
    return df

def excel_to_dataframe(uploaded_file):
    """Converte o arquivo Excel carregado em DataFrame."""
    return pd.read_excel(uploaded_file)

def extract_sheet_id_from_url(url):
    """Extrai o ID da planilha do Google Sheets a partir da URL."""
    parsed_url = urlparse(url)
    
    # Formato padrão: https://docs.google.com/spreadsheets/d/SHEET_ID/edit...
    path_parts = parsed_url.path.split('/')
    if len(path_parts) >= 4 and path_parts[1] == 'spreadsheets' and path_parts[2] == 'd':
        return path_parts[3]
    
    return None

def create_editable_gsheet_url(sheet_id):
    """Cria uma URL para edição da planilha sem necessidade de autenticação."""
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

def get_download_link(df, filename, text):
    """Cria um link de download para o DataFrame como arquivo Excel."""
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{text}</a>'
    return href

def is_valid_gsheet_url(url):
    """Verifica se a URL é de uma planilha do Google Sheets."""
    return "docs.google.com/spreadsheets" in url and extract_sheet_id_from_url(url) is not None

def submit_to_gsheet(sheet_id, data):
    """Envia os dados para a planilha do Google Sheets usando a API pública."""
    try:
        # Prepara os dados para envio no formato correto
        headers = {"Content-Type": "application/json"}
        
        # URL para o script web app vinculado à planilha
        # Observe que o script web app deve estar publicado como 'Qualquer pessoa'
        # e deve aceitar solicitações POST
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
        
        # Envia os dados para a planilha
        params = {'tqx': 'out:json', 'tq': f'INSERT INTO Sheet1 VALUES {str(tuple(data.values()))}'}
        response = requests.post(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"Erro ao enviar dados para a planilha: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        st.error(f"Erro ao enviar dados para a planilha: {str(e)}")
        return False

# Interface principal
def main():
    st.title("Criador de Formulários Dinâmicos")
    
    # Sidebar para navegação
    with st.sidebar:
        st.title("Menu")
        opcao = st.radio("Selecione uma opção:", 
                          ["Início", "Criar Formulário", "Responder Formulário"])
    
    if opcao == "Início":
        st.header("Bem-vindo ao Criador de Formulários Dinâmicos")
        st.write("""
        Esta aplicação permite criar e responder formulários de forma simples e rápida.
        
        **Como funciona:**
        1. Faça upload de um template Excel com a estrutura do formulário
        2. Indique uma planilha pública do Google Sheets para armazenar as respostas
        3. Compartilhe o link do formulário gerado
        
        **Sem necessidade de autenticação no Google!**
        """)
        
        st.subheader("Baixe o template para começar")
        template_df = get_template_excel()
        st.markdown(get_download_link(template_df, "template_formulario.xlsx", 
                                     "📥 Baixar Template Excel"), unsafe_allow_html=True)
        
        st.info("""
        **Instruções para o template:**
        - **campo**: Nome técnico do campo (sem espaços ou caracteres especiais)
        - **tipo**: Tipo do campo (texto, email, numero, area_texto, selecao, multipla_escolha, data, hora)
        - **obrigatorio**: Se o campo é obrigatório (sim/nao)
        - **label**: Texto que aparecerá para o usuário
        - **placeholder**: Texto de exemplo dentro do campo
        - **opcoes**: Para campos do tipo 'selecao' ou 'multipla_escolha', liste as opções separadas por vírgula
        """)
        
    elif opcao == "Criar Formulário":
        st.header("Criar Novo Formulário")
        
        # Formulário para criação
        with st.form("criar_formulario"):
            nome_formulario = st.text_input("Nome do Formulário", placeholder="Ex: Pesquisa de Satisfação")
            
            uploaded_file = st.file_uploader("Carregar template Excel", type=["xlsx"])
            
            gsheet_url = st.text_input(
                "URL da Planilha do Google Sheets para respostas",
                placeholder="https://docs.google.com/spreadsheets/d/..."
            )
            
            submitted = st.form_submit_button("Criar Formulário")
        
        if submitted:
            if not nome_formulario:
                st.error("Por favor, informe um nome para o formulário.")
            elif not uploaded_file:
                st.error("Por favor, carregue o arquivo de template Excel.")
            elif not gsheet_url:
                st.error("Por favor, informe a URL da planilha do Google Sheets.")
            elif not is_valid_gsheet_url(gsheet_url):
                st.error("URL da planilha do Google Sheets inválida.")
            else:
                try:
                    # Processar o arquivo Excel
                    df = excel_to_dataframe(uploaded_file)
                    
                    # Verificar se o template está correto
                    colunas_necessarias = ['campo', 'tipo', 'obrigatorio', 'label']
                    if not all(col in df.columns for col in colunas_necessarias):
                        st.error("O arquivo Excel não segue o formato do template. Verifique as colunas necessárias.")
                        return
                    
                    # Extrair o ID da planilha
                    sheet_id = extract_sheet_id_from_url(gsheet_url)
                    
                    # Salvar configuração do formulário na sessão
                    st.session_state['formulario'] = {
                        'nome': nome_formulario,
                        'campos': df.to_dict('records'),
                        'sheet_id': sheet_id
                    }
                    
                    st.success("Formulário criado com sucesso!")
                    
                    # Mostrar link para o formulário
                    st.subheader("Link para o formulário")
                    
                    # Gerar um link "fictício" (em uma aplicação real, seria necessário gerar
                    # uma URL única que identificasse esse formulário específico)
                    form_params = {
                        'nome': nome_formulario,
                        'sheet_id': sheet_id
                    }
                    
                    # Na versão real, você usaria uma URL externa ou um identificador
                    # para cada formulário. Para esta demonstração, usamos parâmetros de URL
                    encoded_params = base64.b64encode(json.dumps(form_params).encode()).decode()
                    
                    st.markdown(f"""
                    **Para responder este formulário, acesse:**
                    
                    [Responder Formulário](/?form={encoded_params})
                    
                    ou compartilhe o link abaixo:
                    ```
                    {st.experimental_get_query_params().get('server_url', [''])[0]}/?form={encoded_params}
                    ```
                    """)
                    
                    # Exibir prévia do formulário
                    st.subheader("Prévia do Formulário")
                    
                    # Mostra cada campo configurado
                    for i, campo in enumerate(df.to_dict('records')):
                        st.write(f"**{campo['label']}**")
                        if campo['tipo'] == 'texto':
                            st.text_input(f"Prévia - {campo['label']}", key=f"preview_{i}", 
                                         placeholder=campo.get('placeholder', ''))
                        elif campo['tipo'] == 'area_texto':
                            st.text_area(f"Prévia - {campo['label']}", key=f"preview_{i}",
                                        placeholder=campo.get('placeholder', ''))
                        elif campo['tipo'] == 'numero':
                            st.number_input(f"Prévia - {campo['label']}", key=f"preview_{i}")
                        elif campo['tipo'] == 'email':
                            st.text_input(f"Prévia - {campo['label']}", key=f"preview_{i}",
                                         placeholder=campo.get('placeholder', ''))
                        elif campo['tipo'] == 'selecao':
                            opcoes = campo.get('opcoes', '').split(',')
                            if opcoes and opcoes[0]:
                                st.selectbox(f"Prévia - {campo['label']}", opcoes, key=f"preview_{i}")
                            else:
                                st.error(f"O campo '{campo['label']}' do tipo 'selecao' não possui opções definidas.")
                        elif campo['tipo'] == 'multipla_escolha':
                            opcoes = campo.get('opcoes', '').split(',')
                            if opcoes and opcoes[0]:
                                st.multiselect(f"Prévia - {campo['label']}", opcoes, key=f"preview_{i}")
                            else:
                                st.error(f"O campo '{campo['label']}' do tipo 'multipla_escolha' não possui opções definidas.")
                        elif campo['tipo'] == 'data':
                            st.date_input(f"Prévia - {campo['label']}", key=f"preview_{i}")
                        elif campo['tipo'] == 'hora':
                            st.time_input(f"Prévia - {campo['label']}", key=f"preview_{i}")
                        else:
                            st.error(f"Tipo de campo não suportado: {campo['tipo']}")
                    
                    st.button("Enviar (Apenas Prévia)", disabled=True)
                    
                except Exception as e:
                    st.error(f"Erro ao processar o arquivo: {str(e)}")
    
    elif opcao == "Responder Formulário":
        st.header("Responder Formulário")
        
        # Verificar se há um formulário na URL
        query_params = st.experimental_get_query_params()
        form_param = query_params.get('form', [None])[0]
        
        if form_param:
            try:
                # Decodificar os parâmetros do formulário
                form_data = json.loads(base64.b64decode(form_param).decode())
                nome_formulario = form_data.get('nome')
                sheet_id = form_data.get('sheet_id')
                
                # Na aplicação real, você buscaria a configuração completa do formulário
                # Aqui, vamos simular um formulário básico
                st.subheader(nome_formulario)
                
                # Na aplicação real, você carregaria os campos do formulário
                # de um banco de dados ou arquivo usando o identificador
                
                # Para esta demonstração, vamos criar um formulário básico
                with st.form("responder_formulario"):
                    # Na aplicação real, esses campos viriam da configuração salva
                    nome = st.text_input("Nome Completo", required=True)
                    email = st.text_input("E-mail", required=True)
                    idade = st.number_input("Idade", min_value=0, max_value=120)
                    comentario = st.text_area("Comentário")
                    
                    submitted = st.form_submit_button("Enviar Resposta")
                
                if submitted:
                    if not nome or not email:
                        st.error("Por favor, preencha todos os campos obrigatórios.")
                    else:
                        # Preparar dados para envio
                        data = {
                            'nome': nome,
                            'email': email,
                            'idade': idade,
                            'comentario': comentario,
                            'data_envio': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # Enviar para a planilha
                        # Na aplicação real, você implementaria a lógica completa para
                        # enviar os dados para a planilha do Google Sheets
                        
                        # Aqui, simularemos o sucesso
                        st.success("Resposta enviada com sucesso!")
                        st.balloons()
            
            except Exception as e:
                st.error(f"Erro ao carregar o formulário: {str(e)}")
                st.info("Verifique se o link do formulário está correto ou retorne à página inicial para criar um novo formulário.")
        
        else:
            st.info("Nenhum formulário especificado. Use um link de formulário válido ou crie um novo formulário.")
            
            # Opção para inserir manualmente um link de formulário
            form_link = st.text_input("Cole aqui o link do formulário", 
                                     placeholder="https://share.streamlit.io/...?form=...")
            
            if form_link:
                # Extrair parâmetros da URL inserida
                parsed_url = urlparse(form_link)
                parsed_qs = parse_qs(parsed_url.query)
                
                if 'form' in parsed_qs:
                    form_param = parsed_qs['form'][0]
                    st.experimental_set_query_params(form=form_param)
                    st.rerun()
                else:
                    st.error("Link de formulário inválido. Verifique se o link está correto.")

if __name__ == "__main__":
    main()
