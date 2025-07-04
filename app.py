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
                st.session_state["excel_df"] = df
                st.success(f"✅ {len(df)} contatti caricati correttamente.")
                st.dataframe(df[["Name", "Company", "Role", "Triggers"]])
            except Exception as e:
                st.error(f"❌ Errore durante il parsing del file: {e}")
        else:
            st.info("Carica un file Excel per visualizzare i contatti.")

    # 2. Caricamento multiplo PDF
    with st.expander("📄 2. Carica i PDF da usare come input (opzionale)", expanded=True):
        uploaded_pdfs = st.file_uploader("Carica uno o più file PDF", type=["pdf"], accept_multiple_files=True)

        if uploaded_pdfs:
            total_size = sum([f.size for f in uploaded_pdfs]) / (1024 * 1024)  # MB
            if len(uploaded_pdfs) > 10:
                st.warning("⚠️ Hai caricato più di 10 PDF. Consigliato: max 10 alla volta.")
            if total_size > 50:
                st.warning(f"⚠️ Dimensione totale PDF: {total_size:.1f}MB. Potrebbero verificarsi rallentamenti.")

            st.success(f"📄 {len(uploaded_pdfs)} PDF caricati (non ancora memorizzati).")

            if st.button("📌 Memorizza questi PDF"):
                if "pdf_memory" not in st.session_state:
                    st.session_state["pdf_memory"] = []
                st.session_state["pdf_memory"].extend(uploaded_pdfs)
                st.success("PDF aggiunti alla memoria temporanea.")

        # Riepilogo PDF memorizzati
        pdfs_mem = st.session_state.get("pdf_memory", [])
        if pdfs_mem:
            st.info(f"📌 Totale PDF memorizzati: {len(pdfs_mem)}")
            if st.button("🧠 Elabora PDF ora"):
                st.write("📖 Elaborazione in corso...")
                parsed_texts = parse_pdf_files(pdfs_mem)
                st.session_state["parsed_pdf"] = parsed_texts
                for filename, content in parsed_texts.items():
                    with st.expander(f"📄 {filename}", expanded=False):
                        st.markdown("**Testo estratto (parziale):**")
                        st.write(content[:1500] + "..." if len(content) > 1500 else content)
                st.success("✔️ Parsing dei PDF completato.")

    # 3. Azioni della campagna (pulsanti sempre visibili)
    st.markdown("### 🎯 3. Azioni disponibili")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Avvia"):
            df = st.session_state.get("excel_df")
            if df is not None:
                start_campaign_flow(df)
            else:
                st.warning("Carica prima un file Excel per avviare la campagna.")
    with col2:
        if st.button("⏸️ Pausa"):
            st.info("🛑 Campagna in pausa (simulazione).")
    with col3:
        if st.button("🗑️ Azzera"):
            st.session_state.pop("excel_df", None)
            st.session_state.pop("pdf_memory", None)
            st.session_state.pop("parsed_pdf", None)
            st.warning("Dati della campagna azzerati.")

    # 4. Chat con AI assistente
    st.markdown("### 💬 4. Chatta con l’assistente AI")
    user_prompt = st.text_area("Scrivi qui una domanda, incolla un contenuto o chiedi aiuto…")
    if st.button("✉️ Invia alla chat AI"):
        if user_prompt:
            prompt_lower = user_prompt.lower()
            if any(k in prompt_lower for k in ["elabora i pdf", "analizza i pdf", "leggi i file", "estrai contenuti"]):
                pdfs_mem = st.session_state.get("pdf_memory", [])
                if not pdfs_mem:
                    st.warning("⚠️ Nessun PDF memorizzato.")
                else:
                    st.write("🧠 Elaborazione AI in corso sui PDF caricati...")
                    parsed_texts = parse_pdf_files(pdfs_mem)
                    st.session_state["parsed_pdf"] = parsed_texts
                    for filename, content in parsed_texts.items():
                        with st.expander(f"📄 {filename}", expanded=False):
                            st.markdown("**Testo estratto (parziale):**")
                            st.write(content[:1500] + "..." if len(content) > 1500 else content)
                    st.success("✔️ Parsing completato.")
            else:
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
