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
    save_to_library,
    parse_pdf_files,
    analyze_triggers_and_rank,
    generate_personalized_messages,
    generate_multichannel_sequence,
    load_persona_matrix_from_json,
    load_all_buyer_personas,
    save_all_buyer_personas
)
from PIL import Image
import pandas as pd
import io
import matplotlib.pyplot as plt
from io import BytesIO
from docx import Document

# --- CONFIG ---
st.set_page_config(page_title="Flowgent AI", layout="wide")
logo = load_logo()
if logo:
    st.image(logo, width=160)
else:
    st.markdown("### LOGO")

st.title("Ciao 👋 cosa vuoi fare oggi?")

with st.expander("⚙️ Impostazioni utente", expanded=False):
    show_settings()

# --- SIDEBAR ---
st.sidebar.title("📌 Menu")
options = {
    "🚀 Avvia una nuova campagna": "start_campaign",
    "🤖 Simula una conversazione": "simulate",
    "📝 Crea un post LinkedIn": "linkedin_post",
    "🗓️ Cosa devo fare oggi?": "agenda",
    "👤 Buyer Persona": "persona",
    "📊 Analisi Competitor": "competitor"
}
selected_label = st.sidebar.radio("Scegli un'azione", list(options.keys()))
action = options[selected_label]

st.sidebar.title("🧭 Navigazione")
nav_choice = st.sidebar.radio("Vai a…", [
    "🚀 Avvia una nuova campagna",
    "📥 Consulta Report",
    "📚 Apri la tua libreria",
    "💬 Lascia un feedback",
    "🔐 Data privacy & condizioni d’uso",
    "🔄 Aggiornamenti"
], key="nav_choice")

# --- ROUTING PRINCIPALE ---
if action == "persona":
    st.subheader("👤 Crea o modifica una Buyer Persona")

    st.markdown("#### 1️⃣ Cosa fa la tua azienda e qual è la tua value proposition?")
    value_prop = st.text_area("Value Proposition", placeholder="Es: Offriamo una piattaforma BIS per integrare partner EDI/API senza sviluppi custom...")

    st.markdown("#### 2️⃣ Quali sono i 3 pain point principali che risolvi?")
    pain_1 = st.text_input("Pain Point 1")
    pain_2 = st.text_input("Pain Point 2")
    pain_3 = st.text_input("Pain Point 3")

    st.markdown("#### 3️⃣ Per quali ruoli vuoi creare la matrice?")
    roles = st.text_input("Ruoli (separati da virgola)", placeholder="Es: CIO, Supply Chain Manager, EDI Manager")

    st.markdown("#### 📎 Vuoi caricare risorse extra?")
    uploaded_file = st.file_uploader("Carica PDF o Excel (opzionale)", type=["pdf", "xlsx"])
    additional_notes = st.text_area("Note aggiuntive (facoltative)")

    if st.button("💾 Salva Buyer Persona"):
        bp_data = load_all_buyer_personas()
        for role in [r.strip() for r in roles.split(",") if r.strip()]:
            if role not in bp_data:
                bp_data[role] = {"industries": {}}
            bp_data[role]["industries"]["custom"] = {
                "kpi": ["[Da definire]"],
                "pain": [pain_1, pain_2, pain_3],
                "suggestion": value_prop
            }
        save_all_buyer_personas(bp_data)
        st.success("✅ Buyer Persona salvata!")

    with st.expander("📂 Buyer Persona già salvate"):
        buyer_personas = load_all_buyer_personas()
        industries = sorted(set(
            industry
            for role_data in buyer_personas.values()
            for industry in role_data.get("industries", {}).keys()
        ))
        roles = sorted(buyer_personas.keys())

        selected_industry = st.selectbox("📂 Scegli il settore", industries)
        selected_role = st.selectbox("🧑‍💼 Scegli il ruolo", roles)

        selected_data = buyer_personas.get(selected_role, {}).get("industries", {}).get(selected_industry)
        if selected_data:
            st.markdown(f"- **Pain**: {', '.join(selected_data.get('pain', []))}")
            st.markdown(f"- **KPI**: {', '.join(selected_data.get('kpi', []))}")
            st.markdown(f"- **Suggerimento**: {selected_data.get('suggestion', '')}")
        else:
            st.info("❌ Nessuna buyer persona trovata per questa combinazione.")

    st.markdown("---")
    st.markdown("Vuoi usare subito queste informazioni per generare messaggi?")
    if st.button("🚀 Avvia una nuova campagna"):
        st.session_state["nav_choice"] = "🚀 Avvia una nuova campagna"
        st.experimental_rerun()

elif action == "simulate":
    simulate_conversation()

elif action == "linkedin_post":
    generate_post()

elif action == "agenda":
    show_daily_tasks()

elif action == "start_campaign" or nav_choice == "🚀 Avvia una nuova campagna":
    exec(open("campaign_screen.py").read())  # facoltativo: separa in modulo esterno

elif nav_choice == "📥 Consulta Report":
    show_reports()

elif nav_choice == "📚 Apri la tua libreria":
    show_library()

elif nav_choice == "💬 Lascia un feedback":
    show_feedback_form()

elif nav_choice == "🔐 Data privacy & condizioni d’uso":
    show_privacy_policy()

elif nav_choice == "🔄 Aggiornamenti":
    check_for_updates()

else:
    show_screen_zero()
