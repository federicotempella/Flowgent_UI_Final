import streamlit as st
import pandas as pd
import openai
import json
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === Funzioni di caricamento e parsing contatti ===

def parse_uploaded_contacts(file):
    try:
        df = pd.read_excel(file)
    except Exception:
        st.error("Errore nella lettura del file. Assicurati che sia un Excel valido.")
        return None

    expected_columns = [
        "First Name", "Last Name", "Company", "Role", "Email", "LinkedIn Profile",
        "Trigger: Something you read / inferred",
        "Trigger: Interesting LinkedIn Post",
        "Trigger: LinkedIn Signal",
        "Trigger: Contact in Common Relevant",
        "Trigger: Company Signal",
        "Notes"
    ]

    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        st.error(f"Mancano colonne obbligatorie nel file: {', '.join(missing)}")
        return None

    contacts = []
    for _, row in df.iterrows():
        full_name = f"{row['First Name']} {row['Last Name']}".strip()
        triggers = []

        for col in expected_columns[6:11]:
            val = row.get(col, "")
            if pd.notna(val) and str(val).strip():
                triggers.append(f"{col.replace('Trigger: ', '')}: {val.strip()}")

        contact = {
            "name": full_name,
            "company": row["Company"],
            "role": row["Role"],
            "email": row["Email"],
            "linkedin": row["LinkedIn Profile"],
            "triggers": triggers,
            "notes": row["Notes"] if pd.notna(row["Notes"]) else ""
        }
        contacts.append(contact)

    return contacts

# --- FINE PARSING ---


import streamlit as st
import pandas as pd
import openai
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- LOGO ---
def load_logo():
    st.image("logo.png", width=200)

# --- GOOGLE SHEET SETUP ---
def load_google_sheet(sheet_id, tab_name, service_account_json):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(service_account_json), scope)
    gc = gspread.authorize(credentials)
    worksheet = gc.open_by_key(sheet_id).worksheet(tab_name)
    return worksheet

# --- EXCEL UPLOAD ---
def load_uploaded_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Errore nel caricamento del file Excel: {e}")
        return None

def parse_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            return df
        except Exception as e:
            st.error(f"Errore nella lettura del file: {e}")
            return None
    return None

# --- START CAMPAIGN FLOW ---
def start_campaign_flow(df, assistant_id, api_key):
    if df is not None:
        st.success("File caricato correttamente. Avvio della campagna disponibile a breve.")
        st.info("⚠️ Modulo attualmente in fase di implementazione.")
    else:
        st.warning("Carica prima un file Excel valido.")

# --- CONVERSATION SIMULATION ---
def simulate_conversation(prompt, assistant_id, api_key):
    if not prompt:
        return "Inserisci un prompt valido."
    openai.api_key = api_key
    client = openai.OpenAI()
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for message in reversed(messages.data):
        if message.role == "assistant":
            return message.content[0].text.value
    return "Nessuna risposta generata."

# --- POST GENERATION ---
def generate_post(topic, tone, style, assistant_id, api_key):
    if not topic:
        return "Inserisci un argomento valido."
    openai.api_key = api_key
    client = openai.OpenAI()
    prompt = f"Crea un post LinkedIn su: {topic}\nTono: {tone}\nStile: {style}"
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for message in reversed(messages.data):
        if message.role == "assistant":
            return message.content[0].text.value
    return "Nessun post generato."

# --- MODEL UPDATE CHECK ---
def check_for_updates(sheet_id, service_account_json):
    try:
        worksheet = load_google_sheet(sheet_id, "Model_Updates", service_account_json)
        updates = worksheet.get_all_records()
        return updates
    except Exception as e:
        st.error(f"Errore durante il recupero degli aggiornamenti: {e}")
        return []

# --- DAILY TASKS ---
def show_daily_tasks():
    st.subheader("🗓️ Attività di oggi")
    st.info("⚠️ Modulo attualmente in fase di implementazione.")
    # In futuro: recupero da Google Sheet e visualizzazione dinamica

# --- FEEDBACK FORM ---
def show_feedback_form():
    st.subheader("📄 Inserisci feedback o note")
    feedback = st.text_area("Scrivi qui il tuo feedback")
    if st.button("Invia"):
        st.success("Feedback inviato con successo!")
        # In futuro: salvataggio automatico su sheet

# --- CONTACT FORM ---
def show_contact_form():
    st.subheader("📞 Modulo contatto")
    nome = st.text_input("Nome")
    email = st.text_input("Email")
    messaggio = st.text_area("Messaggio")
    if st.button("Invia messaggio"):
        st.success("Messaggio inviato. Ti ricontatteremo a breve.")

# --- UPDATE MODULE ---
def show_update_module(updates):
    st.subheader("🆕 Aggiornamenti del modello")
    if not updates:
        st.info("Nessun aggiornamento disponibile.")
        return
    for update in updates:
        with st.expander(update.get("Titolo", "Aggiornamento")):
            st.markdown(update.get("Descrizione", ""))
            col1, col2 = st.columns(2)
            if col1.button(f"✅ Accetta", key=f"accetta_{update['ID']}"):
                st.success(f"Aggiornamento {update['ID']} accettato!")
            if col2.button(f"❌ Ignora", key=f"ignora_{update['ID']}"):
                st.warning(f"Aggiornamento {update['ID']} ignorato.")
