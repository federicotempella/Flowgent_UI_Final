import streamlit as st
from utils import (
    load_logo,
    simulate_conversation,
    generate_post,
    check_for_updates,
    start_campaign_flow,
    show_daily_tasks,
    show_reports,
    show_library,
    show_feedback_form,
    show_settings,
    show_privacy_policy,
    show_screen_zero,
    parse_excel_file,
    save_to_library
)
from PIL import Image

# UI CONFIG
st.set_page_config(page_title="Flowgent AI", layout="wide")
st.markdown('<link rel="stylesheet" href="style.css">', unsafe_allow_html=True)

# LOGO HEADER
logo = load_logo()
if logo:
    st.image(logo, width=160)
else:
    st.markdown("### LOGO")  # Placeholder visivo

st.title("Ciao 👋 cosa vuoi fare oggi?")

# --- TOOLBAR TOP (Ruolo, modalità, dark mode, ecc.) ---
with st.expander("⚙️ Impostazioni utente", expanded=False):
    show_settings()

# --- SIDEBAR ---
st.sidebar.title("📌 Menu")
action = st.sidebar.radio("Navigazione", [
    "🏠 Schermata iniziale",
    "🚀 Avvia una nuova campagna",
    "🤖 Simula una conversazione",
    "📝 Crea un post LinkedIn",
    "📥 Consulta Report",
    "📚 Apri la tua libreria",
    "🗓️ Cosa devo fare oggi?",
    "💬 Lascia un feedback",
    "🔐 Data privacy & condizioni d’uso",
    "🔄 Aggiornamenti"
])

# --- ROUTING ---
if action == "🏠 Schermata iniziale":
    show_screen_zero()

elif action == "🚀 Avvia una nuova campagna":
    st.subheader("🚀 Avvia una nuova campagna")

    # 1. Caricamento Excel contatti
    with st.expander("📁 1. Carica il file Excel contatti", expanded=True):
        uploaded_file = st.file_uploader("Seleziona il file Excel (.xlsx)", type=["xlsx"], help="Limite massimo consigliato 5MB")
        if uploaded_file:
            try:
                df = parse_excel_file(uploaded_file)
                st.success(f"✅ {len(df)} contatti caricati correttamente.")
                st.dataframe(df[["Name", "Company", "Role", "Triggers"]])
            except Exception as e:
                st.error(f"❌ Errore durante il parsing del file: {e}")
        else:
            st.info("Carica un file Excel per visualizzare i contatti.")

    # 2. Caricamento multiplo PDF
    with st.expander("📄 2. Carica i PDF dei profili LinkedIn (facoltativo)", expanded=True):
        uploaded_pdfs = st.file_uploader("Carica uno o più file PDF", type=["pdf"], accept_multiple_files=True)

        if uploaded_pdfs:
            total_size = sum([f.size for f in uploaded_pdfs]) / (1024 * 1024)  # in MB
            if len(uploaded_pdfs) > 10:
                st.warning("⚠️ Hai caricato più di 10 file. Ti consigliamo di caricarne max 10 alla volta.")
            if total_size > 50:
                st.warning(f"⚠️ Dimensione totale PDF: {total_size:.1f}MB. Potrebbe causare rallentamenti.")

            st.success(f"📄 {len(uploaded_pdfs)} file PDF ricevuti. Non ancora elaborati.")
            if st.button("💾 Salva i PDF in memoria per usarli dopo"):
                st.session_state["pdf_memory"] = uploaded_pdfs
                st.success("PDF memorizzati temporaneamente nella sessione.")
            if st.session_state.get("pdf_memory"):
                st.info(f"📌 {len(st.session_state['pdf_memory'])} PDF attualmente in memoria. Pronti all'elaborazione.")
        else:
            st.info("Puoi caricare i PDF dei profili scaricati da LinkedIn (opzionale).")

    # 3. Azioni della campagna
    st.markdown("### 🎯 3. Azioni disponibili")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Avvia"):
            st.success("Campagna avviata (placeholder).")
    with col2:
        if st.button("⏸️ Pausa"):
            st.info("Campagna in pausa (placeholder).")
    with col3:
        if st.button("🗑️ Azzera"):
            st.session_state.pop("pdf_memory", None)
            st.warning("Campagna azzerata. PDF in memoria rimossi.")

    # 4. Chat assistente AI
    st.markdown("### 💬 4. Chatta con l’assistente AI")
    user_prompt = st.text_area("Scrivi qui una domanda, incolla un contenuto o chiedi aiuto…")
    if st.button("✉️ Invia alla chat AI"):
        if user_prompt:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.6,
            )
            st.markdown("**Risposta AI:**")
            st.write(response.choices[0].message.content)
        else:
            st.warning("Scrivi qualcosa prima di inviare.")

elif action == "🤖 Simula una conversazione":
    simulate_conversation()

elif action == "📝 Crea un post LinkedIn":
    generate_post()

elif action == "📥 Consulta Report":
    show_reports()

elif action == "📚 Apri la tua libreria":
    show_library()

elif action == "🗓️ Cosa devo fare oggi?":
    show_daily_tasks()

elif action == "💬 Lascia un feedback":
    show_feedback_form()

elif action == "🔐 Data privacy & condizioni d’uso":
    show_privacy_policy()

elif action == "🔄 Aggiornamenti":
    check_for_updates()
