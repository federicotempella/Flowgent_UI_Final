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
    with st.expander("📁 1. Carica il file Excel dei contatti", expanded=True):
        uploaded_file = st.file_uploader("Seleziona il file .xlsx", type=["xlsx"])
        if uploaded_file:
            st.success("✅ File Excel caricato correttamente. In attesa di avvio.")
            st.session_state["uploaded_excel"] = uploaded_file
        else:
            st.info("Carica un file Excel per avviare la campagna.")

    # 2. Caricamento opzionale profili PDF
    with st.expander("📄 2. (Opzionale) Carica i PDF dei profili LinkedIn"):
        uploaded_pdfs = st.file_uploader("Carica i PDF dei contatti (massimo 10)", type=["pdf"], accept_multiple_files=True)
        if uploaded_pdfs:
            st.session_state["pdf_profiles"] = uploaded_pdfs
            st.success(f"✅ {len(uploaded_pdfs)} PDF caricati.")
        else:
            st.info("Puoi caricare più PDF, uno per ogni contatto.")

    # 3. Chat GPT assistente (multiuso)
    with st.expander("💬 3. Chatta con l’assistente AI", expanded=False):
        user_prompt = st.text_area("Scrivi una domanda, incolla un contenuto, o chiedi supporto:", key="chat_prompt_campagna")
        if st.button("Invia a GPT", key="chat_submit_campagna"):
            if user_prompt:
                with st.spinner("💡 Elaborazione in corso..."):
                    response = openai.ChatCompletion.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": user_prompt}],
                        temperature=0.7,
                    )
                    st.markdown("### 🧠 Risposta dell’assistente")
                    st.write(response.choices[0].message.content)
            else:
                st.warning("Inserisci qualcosa prima di inviare.")

    # 4. Pulsanti gestione campagna (sempre visibili)
    st.markdown("---")
    st.markdown("### 🛠️ Azioni campagna")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Avvia campagna", use_container_width=True):
            if "uploaded_excel" in st.session_state:
                df = parse_excel_file(st.session_state["uploaded_excel"])
                st.session_state["parsed_df"] = df
                start_campaign_flow(df)
            else:
                st.warning("⚠️ Nessun file Excel caricato.")
    with col2:
        if st.button("🔄 Azzera tutto", use_container_width=True):
            st.session_state.clear()
            st.success("✅ Sessione azzerata.")
    with col3:
        if st.button("⏸️ Pausa", use_container_width=True):
            st.info("⏸️ Campagna in pausa. Puoi riprenderla in seguito.")

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
