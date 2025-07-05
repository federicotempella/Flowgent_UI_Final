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

def save_to_library(tipo, contenuto):
    try:
        sheet = load_google_sheet()
        library_tab = sheet.worksheet("library")
        library_tab.append_row([
            datetime.datetime.now().isoformat(),
            tipo,
            contenuto,
            st.session_state.get("user", "Anonimo")
        ])
        st.success("✅ Contenuto salvato nella tua libreria.")
    except Exception as e:
        st.error(f"Errore nel salvataggio in libreria: {str(e)}")

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
def start_campaign_flow(parsed_df=None):
    if parsed_df is not None:
        st.success(f"{len(parsed_df)} contatti caricati correttamente per la campagna.")
        st.dataframe(parsed_df[["Name", "Company", "Role", "Triggers"]])
    else:
        st.warning("📂 Nessun file caricato. Carica un file Excel per avviare la campagna.")

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
    try:
        sheet = load_google_sheet()
        worksheet = sheet.worksheet("Model_Updates")
        values = worksheet.get_all_values()
        if len(values) <= 1:
            st.info("Nessun aggiornamento disponibile.")
            return
        headers = values[0]
        records = values[1:]
        st.subheader("🔄 Aggiornamenti al modello")
        for i, row in enumerate(records, start=2):  # partendo dalla riga 2
            update = dict(zip(headers, row))
            st.markdown(f"**🆕 {update['Titolo']}** – {update['Descrizione']}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Accetta {update['Titolo']}", key=f"accept_{i}"):
                    worksheet.update_cell(i, headers.index("Accettato_colonna") + 1, "Sì")
                    st.success(f"{update['Titolo']} accettato.")
            with col2:
                if st.button(f"❌ Ignora {update['Titolo']}", key=f"ignore_{i}"):
                    worksheet.update_cell(i, headers.index("Accettato_colonna") + 1, "No")
    except Exception as e:
        st.error(f"Errore nella lettura degli aggiornamenti: {str(e)}")

# === 📅 DAILY TASKS ===
def show_daily_tasks():
    try:
        sheet = load_google_sheet()
        worksheet = sheet.worksheet("UI_Log")
        values = worksheet.get_all_values()
        if len(values) <= 1:
            st.info("Nessuna attività registrata oggi.")
            return
        headers = values[0]
        records = values[1:]
        df = pd.DataFrame(records, columns=headers)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        today = datetime.datetime.now().date()
        filtered = df[df['Timestamp'].dt.date == today]
        st.subheader("📅 Le tue azioni recenti")
        st.dataframe(filtered)
    except Exception as e:
        st.error(f"Errore nella lettura delle attività: {str(e)}")

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
    try:
        sheet = load_google_sheet()
        worksheet = sheet.worksheet("library")
        values = worksheet.get_all_values()
        if len(values) <= 1:
            st.info("La libreria è vuota.")
            return
        headers = values[0]
        records = values[1:]
        df = pd.DataFrame(records, columns=headers)
        st.subheader("📚 La tua libreria")
        st.dataframe(df[["Timestamp", "Tipo", "Contenuto"]])
    except Exception as e:
        st.error(f"Errore nella lettura della libreria: {str(e)}")

# === 📊 REPORTS ===
def show_reports():
    sheet = load_google_sheet()
    st.subheader("📊 Log attività")
    for tab_name in ["UI_Log", "Main_Log"]:
        st.markdown(f"### {tab_name}")
        try:
            worksheet = sheet.worksheet(tab_name)
            values = worksheet.get_all_values()
            if len(values) <= 1:
                st.info(f"Nessun dato disponibile in {tab_name}.")
                continue
            headers = values[0]
            records = values[1:]
            df = pd.DataFrame(records, columns=headers)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Errore nella lettura del foglio {tab_name}: {str(e)}")

# === 🔒 PRIVACY POLICY ===
def show_privacy_policy():
    st.subheader("📄 Data Privacy & Proprietà Intellettuale")
    with open("guide_placeholder.pdf", "rb") as f:
        st.download_button("📥 Scarica policy completa", f, file_name="guide_placeholder.pdf")

# === 🏠 SCREEN 0 ===
def show_screen_zero():
    st.markdown("### 👋 Benvenuto!")
    st.markdown("Questa è la schermata iniziale del Sales Bot. Usa la toolbar a destra per iniziare.")
