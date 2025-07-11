import streamlit as st
import pandas as pd
import base64
import json
import openai
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PyPDF2 import PdfReader

# utils.py

import pandas as pd
import re
# altri import se presenti...

# 🔽 Inserisci subito dopo gli import
import json
import os

def load_persona_matrix_from_json(industry="automotive"):
    path = "data/persona_matrix_extended.json"
    if not os.path.exists(path):
        st.warning(f"⚠️ File persona_matrix_extended.json non trovato in {path}")
        return {}

    with open(path, "r") as f:
        full_matrix = json.load(f)

    # Estrae solo la parte per industry richiesta
    persona_matrix = {}
    for role, data in full_matrix.items():
        if industry in data.get("industries", {}):
            persona_matrix[role] = data["industries"][industry]

    return persona_matrix

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

from PyPDF2 import PdfReader

def parse_pdf_files(pdf_files):
    parsed_results = {}
    for pdf in pdf_files:
        try:
            reader = PdfReader(pdf)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            parsed_results[pdf.name] = text.strip()
        except Exception as e:
            parsed_results[pdf.name] = f"Errore nel parsing: {e}"
    return parsed_results

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

    user = st.text_input("Nome utente (facoltativo)", value=st.session_state.get("user", ""))
    level = st.selectbox("Livello", ["Beginner", "Intermediate", "Advanced"], index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.get("level", "Beginner")))
    lang = st.selectbox("Lingua", ["Italiano", "English"], index=["Italiano", "English"].index(st.session_state.get("lang", "Italiano")))

    if st.button("Salva impostazioni"):
        st.session_state["user"] = user if user else "Anonimo"
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

# === 📊 Trigger → KPI → Messaggio suggerito ===
import pandas as pd

def analyze_triggers_and_rank(df, parsed_pdf=None, manual_input=None, buyer_personas=None):
    results = []

    # Unisci tutte le fonti testo extra in un unico blob
    pdf_text = "\n".join(parsed_pdf.values()) if parsed_pdf else ""
    extra_text = (manual_input or "") + "\n" + pdf_text

    for _, row in df.iterrows():
        name = row.get("Name", "")
        company = row.get("Company", "")
        role = row.get("Role", "")
        trigger = row.get("Triggers", "")

        # Buyer persona match
        persona_data = buyer_personas.get(role, {}) if buyer_personas else {}
        kpi = persona_data.get("kpi", [])
        pain = persona_data.get("pain", [])
        suggestion = persona_data.get("suggestion", "")

        # Trigger enrichment da PDF/manual input se manca
        if not trigger and extra_text:
            # Semplice euristica: cerca il nome/azienda nei testi e recupera contesto
            if name in extra_text or company in extra_text:
                trigger = f"Contenuto trovato in PDF o input AI per {name or company}"

        results.append({
            "Nome": name,
            "Azienda": company,
            "Ruolo": role,
            "Trigger rilevato": trigger,
            "Buyer Persona": role,
            "KPI impattati": ", ".join(kpi),
            "Pain Point": ", ".join(pain),
            "Suggerimento": suggestion
        })

    return pd.DataFrame(results)

# === 🧠 Personalizzazione multivariabile con GPT ===
def generate_personalized_messages(df):
    results = []

    for idx, row in df.iterrows():
        nome = row.get("Name", "")
        azienda = row.get("Company", "")
        ruolo = row.get("Role", "")
        trigger = row.get("Triggers", [])
        settore = st.session_state.get("industry", "non specificato")
        livello = st.session_state.get("level", "Intermediate")

        if isinstance(trigger, list):
            trigger_text = "; ".join(trigger)
        else:
            trigger_text = str(trigger)

        prompt = f"""
Sei un assistente GPT per la scrittura di messaggi B2B.
Devi generare un messaggio personalizzato di primo contatto per:

- Nome: {nome}
- Azienda: {azienda}
- Ruolo: {ruolo}
- Settore: {settore}
- Livello utente: {livello}
- Trigger rilevati: {trigger_text}

Usa tono consultivo se il livello è Advanced o Intermediate.
Includi hook personalizzato e call to action.
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Genera solo il testo del messaggio. Max 600 caratteri."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            message = response.choices[0].message.content
        except Exception as e:
            message = f"❌ Errore GPT: {e}"

        results.append({
            "Name": nome,
            "Company": azienda,
            "Role": ruolo,
            "Messaggio generato": message
        })

    return pd.DataFrame(results)

# utils.py

import json, os

base_file = "data/persona_matrix_extended.json"
custom_file = "data/buyer_personas.json"

def load_all_buyer_personas():
    # 1. Carica le buyer persona di base (precaricate nel modello v3)
    if os.path.exists(base_file):
        with open(base_file, "r") as f:
            base_data = json.load(f)
    else:
        base_data = {}

    # 2. Carica le buyer persona salvate dall'utente
    if os.path.exists(custom_file):
        with open(custom_file, "r") as f:
            custom_data = json.load(f)
    else:
        custom_data = {}

    # 3. Merge: custom_data ha priorità
    merged = base_data.copy()

    for role, role_data in custom_data.items():
        if role not in merged:
            merged[role] = role_data
        else:
            # Merge delle industry: custom ha priorità
            merged[role]["industries"] = {
                **merged[role].get("industries", {}),
                **role_data.get("industries", {})
            }

    return merged


def save_all_buyer_personas(data):
    # Salva solo nel file custom (quelle modificate/aggiunte dall’utente)
    with open(custom_file, "w") as f:
        json.dump(data, f, indent=2)
