
import streamlit as st
import pandas as pd
import base64
import io
import openai
import json
import gspread
from datetime import datetime
from google.oauth2 import service_account

# Inizializza Google Sheet
def load_google_sheet():
    credentials = st.secrets["SERVICE_ACCOUNT_JSON"]
    service_account_info = json.loads(credentials)
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"])
    return sheet

# Caricamento logo
def load_logo(path="logo.png"):
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        st.warning("⚠️ Logo non trovato.")
        return ""

# Caricamento file Excel
def load_uploaded_excel(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            return df
        except Exception as e:
            st.error("Errore nel caricamento Excel.")
    return None

# Parsing contatti Excel avanzato
def parse_uploaded_contacts(df):
    if df is None:
        return pd.DataFrame()
    required_cols = ["Nome", "Cognome", "Ruolo", "Azienda", "Email", "LinkedIn", "Manually Found Trigger"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"⚠️ Colonne mancanti: {', '.join(missing_cols)}")
        return pd.DataFrame()
    df.fillna("", inplace=True)
    df["Manually Found Trigger"] = df["Manually Found Trigger"].apply(lambda x: [t.strip() for t in x.split(";")] if x else [])
    return df

def parse_uploaded_file(uploaded_file):
    df = load_uploaded_excel(uploaded_file)
    parsed_df = parse_uploaded_contacts(df)
    return parsed_df

# Simulazione generazione
def simulate_conversation(contact=None):
    st.success("✅ Simulazione avviata per il contatto.")
    st.info("💡 Questa funzione è un placeholder demo. La logica reale verrà inserita al parsing effettivo del contatto.")

def generate_post(contact=None):
    st.success("✅ Post generato!")
    st.info("📌 Placeholder per generazione contenuto. Integrare modello GPT se necessario.")

def start_campaign_flow():
    st.info("📤 Placeholder per start sequenza campagna. Collega modulo sezione dedicata.")

def check_for_updates():
    sheet = load_google_sheet()
    updates = sheet.worksheet("Model_Updates").get_all_records()
    for upd in updates:
        st.markdown(f"**📌 Update:** {upd['Titolo']} — {upd['Data']}")
        st.markdown(upd['Descrizione'])
        if upd.get("Accettato") != "Sì":
            if st.button(f"✅ Accetta aggiornamento: {upd['Titolo']}", key=upd['Titolo']):
                row_idx = updates.index(upd) + 2
                sheet.worksheet("Model_Updates").update_cell(row_idx, 5, "Sì")

def show_screen_zero():
    st.title("👋 Benvenuto nella tua piattaforma Flowgent AI")
    st.write("Seleziona un’azione dal menu a sinistra per iniziare.")

def show_settings():
    st.header("⚙️ Impostazioni utente")
    with st.form("settings_form"):
        role = st.selectbox("Ruolo", ["AE", "SDR", "Manager"])
        level = st.selectbox("Livello", ["Beginner", "Intermediate", "Advanced"])
        lang = st.selectbox("Lingua", ["Italiano", "English"])
        submitted = st.form_submit_button("Salva impostazioni")
        if submitted:
            st.session_state["user_settings"] = {"role": role, "level": level, "lang": lang}
            st.success("✅ Impostazioni aggiornate.")

def show_privacy_policy():
    st.header("🔐 Data Privacy e Proprietà Intellettuale")
    st.markdown("""
    - I tuoi dati sono al sicuro.
    - Tutto il contenuto generato è di tua proprietà.
    - Nessun dato viene condiviso senza consenso esplicito.
    """)

def show_feedback_form():
    st.header("📝 Lascia un feedback")
    with st.form("feedback_form"):
        user = st.text_input("Nome utente")
        comment = st.text_area("Feedback")
        submitted = st.form_submit_button("Invia")
        if submitted:
            sheet = load_google_sheet()
            sheet.worksheet("UI_Log").append_row([
                datetime.now().isoformat(), user, "", "", "", "", "Feedback", comment, "", "", "No"
            ])
            st.success("✅ Grazie per il tuo feedback!")

def show_contact_form():
    st.info("Modulo contatti in fase di sviluppo.")

def show_update_module():
    check_for_updates()

def show_reports():
    st.header("📊 Report")
    sheet = load_google_sheet()
    df_ui = pd.DataFrame(sheet.worksheet("UI_Log").get_all_records())
    df_main = pd.DataFrame(sheet.worksheet("Main_Log").get_all_records())
    st.subheader("📋 UI_Log")
    st.dataframe(df_ui)
    st.subheader("🧾 Main_Log")
    st.dataframe(df_main)

def show_library():
    st.header("📚 La tua libreria")
    sheet = load_google_sheet()
    records = sheet.worksheet("library").get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        st.info("📭 Nessun elemento salvato.")
    else:
        st.dataframe(df)

def save_to_library(content, categoria="Generico"):
    sheet = load_google_sheet()
    sheet.worksheet("library").append_row([
        datetime.now().isoformat(), st.session_state.get("user_name", "anonimo"), categoria, content
    ])

def show_daily_tasks():
    st.header("📆 Attività giornaliere")
    st.markdown("- 📤 Invio sequenze")
    st.markdown("- 🔁 Follow-up")
    st.markdown("- 📥 Controlla risposte")
    st.markdown("- 📈 Rivedi performance")  
