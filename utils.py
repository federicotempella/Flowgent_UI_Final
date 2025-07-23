import streamlit as st
import pandas as pd
import base64
import json
import re
import openai
import datetime
import gspread
import fitz
from oauth2client.service_account import ServiceAccountCredentials
from PyPDF2 import PdfReader
from date import datetime

# utils.py

import pandas as pd
import re
# altri import se presenti...


import openai

def generate_pain_from_trigger(trigger, ruolo):
    prompt = f"""Mi dai un esempio di pain point che potrebbe avere un {ruolo} se nota questo trigger: {trigger}? Rispondi in 1 frase."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT error: {e}"

def generate_kpi_from_trigger(trigger, ruolo):
    prompt = f"""Quale KPI potrebbe essere impattato per un {ruolo} in presenza di questo trigger: {trigger}? Rispondi in 1 frase."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT error: {e}"

def log_buyer_persona_submission(user_id, role, industry, pain, kpi, suggestion):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("AI_SalesBot_UI_Log").worksheet("BuyerPersona_Log")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet.append_row([
        now,
        user_id,
        role,
        industry,
        ", ".join(pain),
        ", ".join(kpi),
        suggestion,
        "🟡 In attesa approvazione"
    ])


# 🔽 Inserisci subito dopo gli import
import json
import os

def load_persona_matrix_from_json(industry="automotive"):
    path = "resources/buyer_personas_master.json"
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

def generate_multichannel_sequence(contact_df, sequence_type="AE", use_inmail=False):
    sequences = []

    for _, row in contact_df.iterrows():
        name = row.get("Name", "Contatto")
        company = row.get("Company", "Azienda")
        role = row.get("Role", "Ruolo")
        trigger = row.get("Trigger combinato", "")

        step_list = []

        if sequence_type == "AE":
            step_list = [
                "[Giorno 1] ✉️ Email di apertura (TIPPS + COI se score >= 4)",
                "[Giorno 3] 🤝 Richiesta connessione LinkedIn (senza nota)",
                "[Giorno 5] 💬 DM LinkedIn personalizzato (se accetta)",
                "[Giorno 6] 📎 Follow-up email con case study", 
                "[Giorno 8] 💬 DM video / voice note (se non risponde)",
                "[Giorno 10] ✉️ Email bump consultiva",
                "[Giorno 12] 💬 Ultimo DM: chiusura + soft CTA",
                "[Giorno 14] 🧠 Invia asset finale (es. guida, template)"
            ]
            if use_inmail:
                step_list.insert(2, "[Giorno 4] ✉️ InMail teaser (se ignorato)")
        else:  # SDR lunga 11 step
            step_list = [
                "[Giorno 1] ✉️ Email teaser (1-riga, aggancia problema)",
                "[Giorno 2] 🤝 Connessione LinkedIn (senza nota)",
                "[Giorno 3] ✉️ InMail: hook provocatorio + mini payoff",
                "[Giorno 4] 💬 DM breve: 'Curioso come lo affrontate internamente?'",
                "[Giorno 5] 🎙️ Voice Note LinkedIn – max 30 sec, friendly",
                "[Giorno 6] ✉️ Follow-up Email (TIPPS)",
                "[Giorno 7] 📞 Cold Call (se apertura o trigger forte)",
                "[Giorno 9] 💬 Interazione post LinkedIn (like/commento)",
                "[Giorno 11] ✉️ Bump: 'Mando tutto a cestino o ha senso riprendere?'",
                "[Giorno 13] 📎 DM consultivo: case simile + spunto",
                "[Giorno 15] 🏁 Ultimo touch o passa ad AE"
            ]

        # Inserimento automatico CALL o BUMP
        call_trigger_keywords = ["interesse", "ebook", "pdf", "evento", "demo", "profilo", "engagement", "aperto", "letto"]
        bump_keywords = ["nessuna risposta", "ghosting", "non ha risposto", "nessun feedback", "ignorato"]

        if any(k in trigger.lower() for k in call_trigger_keywords):
            step_list.append("[Giorno 16] 📞 Call suggerita – il contatto ha mostrato segnali di interesse")
        elif any(k in trigger.lower() for k in bump_keywords):
            step_list.append("[Giorno 17] ⏪ Bump finale (DM o Email) – stimola reazione se silenzio prolungato")

        sequences.append({
            "Name": name,
            "Company": company,
            "Role": role,
            "Sequenza multicanale": step_list
        })

    return sequences

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
import re
import openai

def analyze_triggers_and_rank(df, parsed_pdf=None, manual_input=None, buyer_personas=None):
    if buyer_personas is None:
        buyer_personas = {}

    def extract_known_triggers(text):
        triggers = []
        for role_data in buyer_personas.values():
            for industry_data in role_data.get("industries", {}).values():
                for p in industry_data.get("pain", []):
                    if p and re.search(re.escape(p), text, re.IGNORECASE):
                        triggers.append(p)
        return list(set(triggers))

    # Unisci Excel + PDF + GPT notes in un solo corpus
    combined_texts = []
    if parsed_pdf:
        for content in parsed_pdf.values():
            combined_texts.append(content)
    if manual_input:
        combined_texts.append(manual_input)

    full_context = " ".join(combined_texts).lower()

    results = []

    for _, row in df.iterrows():
        name = row.get("Name", "Sconosciuto")
        company = row.get("Company", "N/A")
        role = row.get("Role", "N/A")
        trigger_cell = row.get("Triggers", "")
        found_triggers = []

        # Analisi Excel triggers
        for t in re.split(r",|;", str(trigger_cell)):
            t_clean = t.strip().lower()
            if t_clean:
                found_triggers.append(t_clean)

        # Arricchimento: aggiungi anche i trigger trovati in PDF/AI notes
        extra_triggers = extract_known_triggers(full_context)
        all_triggers = list(set(found_triggers + extra_triggers))

        # Calcolo score
        score = len(all_triggers)
        framework = "TIPPS (generico)"
        if score >= 4:
            framework = "TIPPS + COI"
        elif score == 3:
            framework = "NEAT (Harris)"
        elif score == 2:
            framework = "TIPPS"
        elif score == 1:
            framework = "Poke the Bear"

        # Recupera KPI e suggestion da buyer_personas
        kpi_list = []
        suggestion = ""
        for role_key, data in buyer_personas.items():
            if role_key.lower() == role.lower():
                for industry_data in data.get("industries", {}).values():
                    kpi_list += industry_data.get("kpi", [])
                    if not suggestion:
                        suggestion = industry_data.get("suggestion", "")

        # Pulisce e rimuove duplicati
        kpi_list = list(set(kpi_list))
        kpi_str = ", ".join(kpi_list)

        # Costruzione finale
        results.append({
            "Name": name,
            "Company": company,
            "Role": role,
            "Trigger combinato": ", ".join(all_triggers),
            "Score": score,
            "KPI consigliati": kpi_str,
            "Framework suggerito": framework,
            "Suggerimento di messaggio": suggestion
        })

    return pd.DataFrame(results)

# === 🧠 Personalizzazione multivariabile con GPT ===
import openai
import pandas as pd
import json
import os

# Funzione per caricare framework live
def load_frameworks():
    path_master = "resources/frameworks_master.json"
    if os.path.exists(path_master):
        with open(path_master, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def generate_personalized_messages(ranked_df, framework_override=None):
    messages = []
    frameworks_all = load_frameworks()

    for _, row in ranked_df.iterrows():
        nome = row.get("Nome", "")
        azienda = row.get("Azienda", "")
        ruolo = row.get("Ruolo", "")
        trigger = row.get("Trigger rilevato", "")
        kpi = row.get("KPI impattati", "")
        pain = row.get("Pain Point", "")
        framework_id = row.get("Framework", "")

        # Override framework se l'utente ha selezionato uno
        if framework_override and framework_override != "Auto (da score)":
            framework_id = framework_override

        selected_fw = frameworks_all.get(framework_id)
        if not selected_fw:
            structure_text = "TIPPS: Trigger, Issue, Positioning, Proof, Step"
            framework_name = framework_id
            description = ""
        else:
            structure = selected_fw.get("structure", selected_fw.get("rules", []))
            structure_text = "\n".join(f"- {s}" for s in structure)
            framework_name = selected_fw["name"]
            description = selected_fw["description"]

        # PROMPT GPT
        prompt = f"""Scrivi un messaggio outbound seguendo il framework selezionato.

📘 Framework: {framework_name}
📋 Descrizione: {description}

🧩 Struttura:
{structure_text}

📎 Contesto:
- Nome: {nome}
- Azienda: {azienda}
- Ruolo: {ruolo}
- Trigger: {trigger}
- KPI: {kpi}
- Pain: {pain}

Obiettivo: ottenere risposta o apertura. Tono diretto, rilevante e professionale.
Evita frasi generiche. Concludi con una call-to-action soft.
"""

        try:
            completion = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
            )
            message = completion.choices[0].message.content.strip()
        except Exception as e:
            message = f"Errore GPT: {e}"

        messages.append({
            "Nome": nome,
            "Azienda": azienda,
            "Ruolo": ruolo,
            "Messaggio generato": message
        })

    return pd.DataFrame(messages)

# utils.py

import streamlit as st
import json, os

base_file = "resources/buyer_personas_master.json"
custom_file = "resources/buyer_personas.json"

def load_all_buyer_personas():
    base_data = {}
    custom_data = {}
    live_data = st.session_state.get("buyer_personas_live", {})

    if os.path.exists(base_file):
        with open(base_file, "r", encoding="utf-8") as f:
            base_data = json.load(f)

    if os.path.exists(custom_file):
        with open(custom_file, "r", encoding="utf-8") as f:
            custom_data = json.load(f)

    # Merge con priorità: live > custom > base
    merged = base_data.copy()

    for role, role_data in custom_data.items():
        if role not in merged:
            merged[role] = role_data
        else:
            merged[role]["industries"] = {
                **merged[role].get("industries", {}),
                **role_data.get("industries", {})
            }

    for role, role_data in live_data.items():
        if role not in merged:
            merged[role] = role_data
        else:
            merged[role]["industries"] = {
                **merged[role].get("industries", {}),
                **role_data.get("industries", {})
            }

    return merged

def save_all_buyer_personas(data):
    # Salva solo nel file custom (quelle modificate/aggiunte dall’utente)
    with open(custom_file, "w") as f:
        json.dump(data, f, indent=2)
