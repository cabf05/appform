import streamlit as st
from supabase import create_client
import random
import time
import io
from PIL import Image, ImageDraw, ImageFont

# --- Initial Setup ---
st.set_page_config(page_title="Number Assignment", layout="centered")

# --- Function to Connect to Supabase ---
def get_supabase_client():
    supabase_url = st.session_state.get("SUPABASE_URL")
    supabase_key = st.session_state.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        st.error("Supabase configuration not found. Go to 'Configuration'.")
        return None
    return create_client(supabase_url, supabase_key)

# --- Sidebar Navigation ---
st.sidebar.title("Menu")
page = st.sidebar.radio("Choose an option", ["Configuration", "Manage Meetings", "Assign Number"])

# --- Page 1: Configuration ---
if page == "Configuration":
    st.title("Supabase Configuration")

    supabase_url = st.text_input("Supabase URL", type="default")
    supabase_key = st.text_input("Supabase API Key", type="password")

    if st.button("Save Configuration"):
        st.session_state["SUPABASE_URL"] = supabase_url
        st.session_state["SUPABASE_KEY"] = supabase_key
        st.success("Configuration saved successfully!")

# --- Page 2: Manage Meetings ---
elif page == "Manage Meetings":
    st.title("Manage Meetings")
    supabase = get_supabase_client()
    if not supabase:
        st.stop()

    meeting_name = st.text_input("Meeting Name")

    if st.button("Create New Meeting"):
        if meeting_name:
            table_name = f"meeting_{int(time.time())}"
            data = [{"Number": i, "Assigned": False} for i in range(1, 1000)]

            supabase.table(table_name).insert(data).execute()

            meeting_link = f"https://yourapp.streamlit.app/?page=assign&table={table_name}"
            st.success(f"Meeting created! Share this link: {meeting_link}")
        else:
            st.warning("Enter a meeting name.")

# --- Page 3: Assign Number ---
elif page == "Assign Number":
    st.title("Get Your Number")

    # Retrieve parameters from the URL
    query_params = st.experimental_get_query_params()
    table_name = query_params.get("table", [None])[0]

    if not table_name:
        st.error("Invalid table.")
        st.stop()

    supabase = get_supabase_client()
    if not supabase:
        st.stop()

    # Check if the user already has an assigned number stored in the session
    if "assigned_number" not in st.session_state:
        response = supabase.table(table_name).select("*").eq("Assigned", False).execute()

        if response.data:
            available_numbers = [row["Number"] for row in response.data]
            assigned_number = random.choice(available_numbers)

            supabase.table(table_name).update({"Assigned": True}).eq("Number", assigned_number).execute()

            st.session_state["assigned_number"] = assigned_number
        else:
            st.error("All numbers have already been assigned!")
            st.stop()

    st.write(f"Your assigned number is: **{st.session_state['assigned_number']}**")

    if st.button("Save as Image"):
        st.session_state["save_as_image"] = True

    if st.session_state.get("save_as_image"):
        number = st.session_state["assigned_number"]
        img = Image.new("RGB", (400, 200), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((150, 80), str(number), font=font, fill=(0, 0, 0))

        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        st.image(img_buffer)
        st.download_button("Download Image", img_buffer, file_name="my_number.png", mime="image/png")
