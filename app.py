import streamlit as st
from supabase import create_client, Client
import random
import time
import io
import uuid
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from datetime import datetime

# --- Initial Setup ---
st.set_page_config(
    page_title="Sistema de Atribuição de Números",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .main-header {text-align: center; margin-bottom: 30px;}
    .number-display {font-size: 72px; text-align: center; margin: 30px 0;}
    .success-msg {background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px;}
    .error-msg {background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# --- Function to Connect to Supabase ---
def get_supabase_client() -> Client:
    """Estabelece conexão com o Supabase usando as credenciais armazenadas na sessão."""
    supabase_url = st.session_state.get("SUPABASE_URL")
    supabase_key = st.session_state.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        st.error("Configuração do Supabase não encontrada. Vá para 'Configuração'.")
        return None
    
    try:
        client = create_client(supabase_url, supabase_key)
        # Teste de conexão simples
        client.table("_dummy").select("*").limit(1).execute()
        return client
    except Exception as e:
        st.error(f"Erro ao conectar com o Supabase: {str(e)}")
        return None

# --- Function to Check if Table Exists ---
def check_table_exists(supabase, table_name):
    """Verifica se uma tabela específica existe no Supabase."""
    try:
        # Esta consulta só terá sucesso se a tabela existir
        response = supabase.table(table_name).select("*").limit(1).execute()
        return True
    except Exception:
        return False

# --- Function to Create Meeting Table ---
def create_meeting_table(supabase, table_name, meeting_name, max_number=999):
    """Cria uma nova tabela para uma reunião no Supabase."""
    try:
        # Tabela de metadados para armazenar informações das reuniões
        if not check_table_exists(supabase, "meetings_metadata"):
            # Cria a tabela de metadados se não existir
            supabase.table("meetings_metadata").insert({
                "id": 1,  # Dummy record to ensure table creation
                "created_at": datetime.now().isoformat()
            }).execute()
            
        # Registrar os metadados da reunião
        supabase.table("meetings_metadata").insert({
            "table_name": table_name,
            "meeting_name": meeting_name,
            "created_at": datetime.now().isoformat(),
            "max_number": max_number
        }).execute()
        
        # Preparar dados para a tabela da reunião (inserir em lotes para evitar sobrecarga)
        batch_size = 100
        for i in range(0, max_number, batch_size):
            end = min(i + batch_size, max_number)
            data = [{"number": j, "assigned": False, "assigned_at": None, "user_id": None} 
                   for j in range(i+1, end+1)]
            
            supabase.table(table_name).insert(data).execute()
            
        return True
    except Exception as e:
        st.error(f"Erro ao criar tabela da reunião: {str(e)}")
        return False

# --- Function to Get Available Meetings ---
def get_available_meetings(supabase):
    """Obtém a lista de reuniões disponíveis."""
    try:
        response = supabase.table("meetings_metadata").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao obter reuniões: {str(e)}")
        return []

# --- Function to Generate and Save Image ---
def generate_number_image(number):
    """Gera uma imagem com o número atribuído."""
    # Criar uma imagem melhor com fundo gradiente
    width, height = 600, 300
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Desenhar um fundo com gradiente simples
    for y in range(height):
        r = int(220 - y/3)
        g = int(240 - y/3)
        b = 255
        for x in range(width):
            draw.point((x, y), fill=(r, g, b))
    
    # Adicionar um texto melhor
    try:
        # Tentar carregar uma fonte melhor, se disponível
        font = ImageFont.truetype("Arial", 120)
    except IOError:
        # Caso a fonte não esteja disponível, usar a padrão
        font = ImageFont.load_default()
    
    # Desenhar o número
    number_text = str(number)
    text_width = draw.textlength(number_text, font=font)
    text_position = ((width - text_width) // 2, height // 2 - 60)
    draw.text(text_position, number_text, font=font, fill=(0, 0, 100))
    
    # Adicionar texto de rodapé
    footer_text = "Seu número para o evento"
    footer_font = ImageFont.load_default()
    footer_width = draw.textlength(footer_text, font=footer_font)
    footer_position = ((width - footer_width) // 2, height - 30)
    draw.text(footer_position, footer_text, font=footer_font, fill=(80, 80, 80))
    
    # Converter para buffer
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    
    return img_buffer

# --- Initialize Session State Variables ---
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())

# --- Sidebar Navigation ---
st.sidebar.title("Menu")
page = st.sidebar.radio("Escolha uma opção", [
    "Configuração", 
    "Gerenciar Reuniões", 
    "Atribuir Número",
    "Ver Estatísticas"
])

# --- Page 1: Configuration ---
if page == "Configuração":
    st.markdown("<h1 class='main-header'>Configuração do Supabase</h1>", unsafe_allow_html=True)
    
    # Recuperar valores salvos, se existirem
    saved_url = st.session_state.get("SUPABASE_URL", "")
    saved_key = st.session_state.get("SUPABASE_KEY", "")
    
    with st.form("config_form"):
        supabase_url = st.text_input("URL do Supabase", value=saved_url)
        supabase_key = st.text_input("Chave API do Supabase", type="password", value=saved_key)
        submit_button = st.form_submit_button("Salvar Configuração")
        
        if submit_button:
            if supabase_url and supabase_key:
                # Salvar na sessão
                st.session_state["SUPABASE_URL"] = supabase_url
                st.session_state["SUPABASE_KEY"] = supabase_key
                
                # Testar a conexão
                try:
                    client = create_client(supabase_url, supabase_key)
                    # Simples teste de conexão
                    client.table("_dummy").select("*").limit(1).execute()
                    st.success("Configuração salva e conexão testada com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao testar conexão: {str(e)}")
            else:
                st.warning("Por favor, preencha todos os campos.")
    
    # Instruções de como configurar o Supabase
    with st.expander("Como configurar o Supabase"):
        st.markdown("""
        1. Crie uma conta no [Supabase](https://supabase.com/)
        2. Crie um novo projeto
        3. Vá para Configurações > API
        4. Copie a URL e a chave anon/public
        5. Cole nos campos acima
        
        **Importante**: Você precisará configurar as seguintes tabelas no SQL Editor do Supabase:
        
        ```sql
        -- Tabela de metadados das reuniões
        create table public.meetings_metadata (
            id bigint generated by default as identity primary key,
            table_name text not null,
            meeting_name text not null,
            created_at timestamp with time zone default timezone('utc'::text, now()) not null,
            max_number integer default 999
        );
        
        -- Exemplo de tabela de reunião (será criada automaticamente pelo app)
        create table public.meeting_example (
            id bigint generated by default as identity primary key,
            number integer not null,
            assigned boolean default false,
            assigned_at timestamp with time zone,
            user_id text
        );
        
        -- Permissões para acesso anônimo (adapte conforme sua política de segurança)
        alter table public.meetings_metadata enable row level security;
        alter table public.meeting_example enable row level security;
        
        create policy "Anon can select meetings_metadata" on public.meetings_metadata for select using (true);
        create policy "Anon can insert meetings_metadata" on public.meetings_metadata for insert with check (true);
        
        create policy "Anon can select meeting_example" on public.meeting_example for select using (true);
        create policy "Anon can update meeting_example" on public.meeting_example for update using (true);
        create policy "Anon can insert meeting_example" on public.meeting_example for insert with check (true);
        ```
        """)

# --- Page 2: Manage Meetings ---
elif page == "Gerenciar Reuniões":
    st.markdown("<h1 class='main-header'>Gerenciar Reuniões</h1>", unsafe_allow_html=True)
    
    supabase = get_supabase_client()
    if not supabase:
        st.stop()
    
    # Interface para criar nova reunião
    with st.form("create_meeting_form"):
        st.subheader("Criar Nova Reunião")
        meeting_name = st.text_input("Nome da Reunião")
        max_number = st.number_input("Número Máximo", min_value=10, max_value=10000, value=999)
        submit_button = st.form_submit_button("Criar Reunião")
        
        if submit_button:
            if meeting_name:
                with st.spinner("Criando reunião..."):
                    # Criar nome da tabela (alfanumérico seguro para SQL)
                    table_name = f"meeting_{int(time.time())}_{meeting_name.lower().replace(' ', '_')}"
                    
                    # Verificar se a tabela já existe
                    if check_table_exists(supabase, table_name):
                        st.error(f"Já existe uma reunião com este nome. Tente outro nome.")
                    else:
                        # Criar a tabela da reunião
                        success = create_meeting_table(supabase, table_name, meeting_name, max_number)
                        
                        if success:
                            # Gerar link para compartilhar
                            meeting_link = f"?page=assign&table={table_name}"
                            st.markdown(f"""
                            <div class="success-msg">
                                <h3>Reunião criada com sucesso!</h3>
                                <p>Compartilhe este link para os participantes:</p>
                                <code>{meeting_link}</code>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Botão para copiar link
                            st.text_input("Copie este link", value=meeting_link)
            else:
                st.warning("Digite um nome para a reunião.")
    
    # Listar reuniões existentes
    st.subheader("Reuniões Existentes")
    
    meetings = get_available_meetings(supabase)
    if meetings:
        meeting_data = []
        for meeting in meetings:
            if "table_name" in meeting and "meeting_name" in meeting:
                # Contar números atribuídos
                try:
                    count_response = supabase.table(meeting["table_name"]).select("*", count="exact").eq("assigned", True).execute()
                    assigned_count = count_response.count if hasattr(count_response, 'count') else 0
                    
                    # Obter estatísticas
                    meeting_data.append({
                        "Nome": meeting.get("meeting_name", "Sem nome"),
                        "Tabela": meeting.get("table_name", ""),
                        "Criada em": meeting.get("created_at", "")[:16].replace("T", " "),
                        "Números Atribuídos": assigned_count,
                        "Total de Números": meeting.get("max_number", 0)
                    })
                except Exception:
                    # Se a tabela não existir mais, pular
                    continue
        
        if meeting_data:
            # Exibir as reuniões em uma tabela
            df = pd.DataFrame(meeting_data)
            st.dataframe(df)
            
            # Opção para deletar reuniões
            with st.expander("Deletar Reunião"):
                selected_meeting = st.selectbox("Selecione a reunião para deletar", 
                                               [m["Tabela"] for m in meeting_data])
                if st.button("Deletar Reunião", type="primary"):
                    try:
                        # Remover da tabela de metadados
                        supabase.table("meetings_metadata").delete().eq("table_name", selected_meeting).execute()
                        
                        # Tentar deletar a tabela da reunião (isso pode não ser permitido dependendo da configuração do Supabase)
                        # Em caso real, você pode precisar de funções SQL específicas para isso
                        st.success(f"Metadados da reunião '{selected_meeting}' deletados. A tabela ainda pode existir no banco de dados.")
                    except Exception as e:
                        st.error(f"Erro ao deletar reunião: {str(e)}")
        else:
            st.info("Não há reuniões disponíveis.")
    else:
        st.info("Não há reuniões disponíveis.")

# --- Page 3: Assign Number ---
elif page == "Atribuir Número":
    st.markdown("<h1 class='main-header'>Obtenha Seu Número</h1>", unsafe_allow_html=True)
    
    # Recuperar parâmetros da URL
    query_params = st.query_params
    table_name = query_params.get("table", None)
    
    if not table_name:
        st.error("Tabela não especificada. Verifique o link compartilhado.")
        
        # Oferecer opção de selecionar uma reunião
        supabase = get_supabase_client()
        if supabase:
            meetings = get_available_meetings(supabase)
            if meetings:
                meeting_options = [f"{m.get('meeting_name', 'Sem nome')} ({m.get('table_name', '')})" for m in meetings]
                selected = st.selectbox("Selecione uma reunião:", meeting_options)
                if selected:
                    selected_table = selected.split("(")[1].split(")")[0]
                    st.markdown(f"[Ir para esta reunião](?page=assign&table={selected_table})")
        st.stop()
    
    supabase = get_supabase_client()
    if not supabase:
        st.stop()
    
    # Verificar se a tabela existe
    if not check_table_exists(supabase, table_name):
        st.error("Tabela da reunião não encontrada. A reunião pode ter sido encerrada.")
        st.stop()
    
    # Obter informações da reunião
    try:
        meeting_info = supabase.table("meetings_metadata").select("*").eq("table_name", table_name).execute()
        meeting_name = meeting_info.data[0]["meeting_name"] if meeting_info.data else "Reunião"
        st.subheader(f"Reunião: {meeting_name}")
    except Exception:
        st.subheader("Obter número para a reunião")
    
    # Gerar um ID de usuário único se não existir
    user_id = st.session_state.get("user_id")
    
    # Verificar se o usuário já tem um número atribuído
    try:
        existing = supabase.table(table_name).select("*").eq("user_id", user_id).execute()
        
        if existing.data:
            # Usuário já tem um número
            st.session_state["assigned_number"] = existing.data[0]["number"]
            st.markdown(f"""
            <div class="success-msg">
                <p>Você já tem um número atribuído:</p>
                <div class="number-display">{st.session_state['assigned_number']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Se o número não foi atribuído ainda
            if "assigned_number" not in st.session_state:
                with st.spinner("Atribuindo um número..."):
                    # Pegar números disponíveis
                    response = supabase.table(table_name).select("*").eq("assigned", False).execute()
                    
                    if response.data:
                        available_numbers = [row["number"] for row in response.data]
                        assigned_number = random.choice(available_numbers)
                        
                        # Atualizar no Supabase
                        supabase.table(table_name).update({
                            "assigned": True, 
                            "assigned_at": datetime.now().isoformat(),
                            "user_id": user_id
                        }).eq("number", assigned_number).execute()
                        
                        st.session_state["assigned_number"] = assigned_number
                    else:
                        st.error("Todos os números já foram atribuídos!")
                        
                        # Mostrar estatísticas
                        total = supabase.table(table_name).select("*", count="exact").execute()
                        st.write(f"Total de números na reunião: {total.count if hasattr(total, 'count') else 'N/A'}")
                        st.stop()
            
            # Exibir o número atribuído
            st.markdown(f"""
            <div class="success-msg">
                <p>Seu número atribuído é:</p>
                <div class="number-display">{st.session_state['assigned_number']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erro ao atribuir número: {str(e)}")
        st.stop()
    
    # Opção para salvar como imagem
    if st.button("Salvar como Imagem"):
        with st.spinner("Gerando imagem..."):
            img_buffer = generate_number_image(st.session_state["assigned_number"])
            st.image(img_buffer)
            st.download_button(
                "Baixar Imagem", 
                img_buffer, 
                file_name=f"meu_numero_{st.session_state['assigned_number']}.png", 
                mime="image/png"
            )

# --- Page 4: Statistics ---
elif page == "Ver Estatísticas":
    st.markdown("<h1 class='main-header'>Estatísticas de Reuniões</h1>", unsafe_allow_html=True)
    
    supabase = get_supabase_client()
    if not supabase:
        st.stop()
    
    # Listar reuniões disponíveis
    meetings = get_available_meetings(supabase)
    if not meetings:
        st.info("Não há reuniões disponíveis para análise.")
        st.stop()
    
    meeting_options = [f"{m.get('meeting_name', 'Sem nome')} ({m.get('table_name', '')})" for m in meetings]
    selected = st.selectbox("Selecione uma reunião:", meeting_options)
    
    if selected:
        # Extrair nome da tabela
        selected_table = selected.split("(")[1].split(")")[0]
        
        try:
            # Obter estatísticas básicas
            total_response = supabase.table(selected_table).select("*", count="exact").execute()
            total_numbers = total_response.count if hasattr(total_response, 'count') else 0
            
            assigned_response = supabase.table(selected_table).select("*", count="exact").eq("assigned", True).execute()
            assigned_numbers = assigned_response.count if hasattr(assigned_response, 'count') else 0
            
            # Calcular percentual
            if total_numbers > 0:
                percentage = (assigned_numbers / total_numbers) * 100
            else:
                percentage = 0
            
            # Exibir estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Números", total_numbers)
            with col2:
                st.metric("Números Atribuídos", assigned_numbers)
            with col3:
                st.metric("Percentual Atribuído", f"{percentage:.1f}%")
            
            # Obter dados temporais se disponíveis
            try:
                time_data_response = supabase.table(selected_table).select("*").eq("assigned", True).order("assigned_at").execute()
                if time_data_response.data:
                    # Processar dados para gráfico
                    time_data = []
                    for item in time_data_response.data:
                        if item.get("assigned_at"):
                            time_data.append({
                                "time": item.get("assigned_at")[:16].replace("T", " "),
                                "count": 1
                            })
                    
                    if time_data:
                        # Agrupar por hora
                        df = pd.DataFrame(time_data)
                        df["time"] = pd.to_datetime(df["time"])
                        df["hour"] = df["time"].dt.floor("H")
                        hourly_counts = df.groupby("hour").count().reset_index()
                        hourly_counts["hour_str"] = hourly_counts["hour"].dt.strftime("%d/%m %H:00")
                        
                        # Plotar gráfico
                        st.subheader("Atribuições de Números por Hora")
                        st.bar_chart(data=hourly_counts, x="hour_str", y="count")
            except Exception:
                st.info("Dados temporais não disponíveis para esta reunião.")
            
            # Opção para exportar dados
            if st.button("Exportar Dados"):
                try:
                    all_data_response = supabase.table(selected_table).select("*").execute()
                    if all_data_response.data:
                        df = pd.DataFrame(all_data_response.data)
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "Baixar CSV", 
                            csv, 
                            file_name=f"{selected_table}_export.csv", 
                            mime="text/csv"
                        )
                except Exception as e:
                    st.error(f"Erro ao exportar dados: {str(e)}")
                    
        except Exception as e:
            st.error(f"Erro ao obter estatísticas: {str(e)}")
