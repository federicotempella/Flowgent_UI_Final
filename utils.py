import streamlit as st
import pandas as pd
import base64
import json
import openai
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === Setup: credenziali da secrets ===
openai.api_key = st.secrets["OPENAI_API_KEY"]
assistant_id = st.secrets["ASSISTANT_ID"]
sheet_id = st.secrets["GOOGLE_SHEET_ID"]
service_account_info = json.loads(st.secrets["SERVICE_ACCOUNT_JSON"])

# === Setup: Google Sheets ===
def load_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)

# === Branding ===
def load_logo(path="logo.png"):
    try:
        with open(path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        st.warning("⚠️ Logo non trovato. Verrà usato un placeholder.")
        return None

# === 📁 Upload & Parsing Excel ===
def load_uploaded_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    return df

def parse_uploaded_file(uploaded_file):
    df = load_uploaded_excel(uploaded_file)
    df = df.dropna(how='all')  # rimuove righe vuote

    # Validazione colonne
    expected_cols = [
        "Name", "Company", "Role", "LinkedIn", 
        "Manually Found Trigger - Something you read / inferred", 
        "Manually Found Trigger - Interesting LinkedIn Post", 
        "Manually Found Trigger - LinkedIn Signal", 
        "Manually Found Trigger - Contact in Common Relevant", 
        "Manually Found Trigger - Company Signal"
    ]
    for col in expected_cols:
        if col not in df.columns:
            raise ValueError(f"Colonna mancante: {col}")

    # Gestione trigger: concatenazione in lista
    def extract_triggers(row):
        triggers = []
        for col in expected_cols[4:]:
            value = row.get(col)
            if pd.notna(value):
                split_values = [v.strip() for v in str(value).split(";") if v.strip()]
                triggers.extend(split_values)
        return triggers

    df["Triggers"] = df.apply(extract_triggers, axis=1)
    return df

def parse_excel_file(uploaded_file):
    return parse_uploaded_file(uploaded_file)

# === 🎯 CAMPAGNA ===
def start_campaign_flow(parsed_df):
    st.success(f"{len(parsed_df)} contatti caricati correttamente per la campagna.")
    st.dataframe(parsed_df[["Name", "Company", "Role", "Triggers"]])

# === 🤖 SIMULATORE ===
def simulate_conversation():
    st.subheader("🤖 Simulatore GPT")
    user_input = st.text_area("Scrivi un prompt...")
    if st.button("Invia"):
        if user_input:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": user_input}],
                temperature=0.7,
            )
            st.write("**Risposta GPT:**", response.choices[0].message.content)
        else:
            st.warning("Inserisci un prompt prima di inviare.")

# === 📬 POST GENERATOR ===
def generate_post():
    st.subheader("✍️ Generatore di contenuti")
    idea = st.text_input("Idea o tema del post:")
    tone = st.selectbox("Tono", ["Professionale", "Informale", "Provocatorio"])
    if st.button("Genera post"):
        if idea:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"Genera un post LinkedIn in tono {tone}."},
                    {"role": "user", "content": idea}
                ],
                temperature=0.8,
            )
            post = response.choices[0].message.content
            st.text_area("Post generato", post, height=200)
            if st.button("💾 Salva in libreria"):
                save_to_library("Post LinkedIn", post)
                st.success("Post salvato nella tua libreria.")
        else:
            st.warning("Inserisci un'idea per generare il post.")

# === 🔁 AGGIORNAMENTI MODELLO ===
def check_for_updates():
    sheet = load_google_sheet()
    update_tab = sheet.worksheet("Model_Updates")
    updates = update_tab.get_all_records()
    st.subheader("🔄 Aggiornamenti al modello")
    for update in updates:
        st.markdown(f"**🆕 {update['Titolo']}** – {update['Descrizione']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Accetta {update['Titolo']}"):
                update_tab.update_cell(update['Riga'], update['Accettato_colonna'], "Sì")
                st.success(f"{update['Titolo']} accettato.")
        with col2:
            if st.button(f"❌ Ignora {update['Titolo']}"):
                update_tab.update_cell(update['Riga'], update['Accettato_colonna'], "No")

# === 📅 DAILY TASKS ===
def show_daily_tasks():
    sheet = load_google_sheet()
    log = sheet.worksheet("UI_Log").get_all_records()
    st.subheader("📅 Le tue azioni recenti")
    df = pd.DataFrame(log)
    if not df.empty:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        today = datetime.datetime.now().date()
        filtered = df[df['Timestamp'].dt.date == today]
        st.dataframe(filtered)
    else:
        st.info("Nessuna attività registrata oggi.")

# === 📋 FEEDBACK FORM ===
def show_feedback_form():
    st.subheader("📝 Lascia un feedback")
    feedback = st.text_area("Il tuo feedback...")
    if st.button("Invia feedback"):
        if feedback:
            sheet = load_google_sheet()
            feedback_tab = sheet.worksheet("UI_Log")
            feedback_tab.append_row([
                datetime.datetime.now().isoformat(),
                st.session_state.get("user", "Anonimo"),
                st.session_state.get("email", ""),
                st.session_state.get("role", ""),
                st.session_state.get("level", ""),
                st.session_state.get("lang", ""),
                "Feedback",
                feedback,
                "", "", ""
            ])
            st.success("Feedback inviato!")
        else:
            st.warning("Scrivi qualcosa prima di inviare.")

# === 💡 SETTINGS ===
def show_settings():
    st.subheader("⚙️ Modifica le tue impostazioni")
    level = st.selectbox("Livello", ["Beginner", "Intermediate", "Advanced"])
    lang = st.selectbox("Lingua", ["Italiano", "English"])
    if st.button("Salva impostazioni"):
        st.session_state["level"] = level
        st.session_state["lang"] = lang
        st.success("Impostazioni aggiornate.")

# === 📚 LIBRERIA ===
def show_library():
    sheet = load_google_sheet()
    lib = sheet.worksheet("library").get_all_records()
    df = pd.DataFrame(lib)
    st.subheader("📚 La tua libreria")
    if df.empty:
        st.info("La libreria è vuota.")
    else:
        st.dataframe(df[["Timestamp", "Tipo", "Contenuto"]])

def save_to_library(tipo, contenuto):
    sheet = load_google_sheet()
    library_tab = sheet.worksheet("library")
    library_tab.append_row([
        datetime.datetime.now().isoformat(),
        tipo,
        contenuto,
        st.session_state.get("user", "Anonimo")
    ])

# === 📊 REPORTS ===
def show_reports():
    sheet = load_google_sheet()
    st.subheader("📊 Log attività")
    for tab_name in ["UI_Log", "Main_Log"]:
        st.markdown(f"### {tab_name}")
        tab = sheet.worksheet(tab_name).get_all_records()
        df = pd.DataFrame(tab)
        if not df.empty:
            st.dataframe(df)
        else:
            st.info(f"Nessun dato in {tab_name}")

# === 🔒 PRIVACY POLICY ===
def show_privacy_policy():
    st.subheader("📄 Data Privacy & Proprietà Intellettuale")
    with open("guide_placeholder.pdf", "rb") as f:
        st.download_button("📥 Scarica policy completa", f, file_name="guide_placeholder.pdf")

# === 🏠 SCREEN 0 ===
def show_screen_zero():
    st.markdown("### 👋 Benvenuto!")
    st.markdown("Questa è la schermata iniziale del Sales Bot. Usa la toolbar a destra per iniziare.")
