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
    
    uploaded_file = st.file_uploader("Carica Excel contatti", type=["xlsx"], help="Limite 200MB per file")

    if uploaded_file:
        df = parse_excel_file(uploaded_file)
        start_campaign_flow(df)
    else:
        st.warning("Carica un file Excel per iniziare la campagna.")

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
