import streamlit as st
import json
import os
from PIL import Image
import pandas as pd
import io
import matplotlib.pyplot as plt
from io import BytesIO
from docx import Document
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
    save_all_buyer_personas,
    buyer_personas.json,
    buyer_personas_master.json,
    frameworks_master.json

)

def load_json(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# --- Qui inserisci la funzione ---
def load_resource(resource_type: str) -> dict:
    live = st.session_state.get(f"{resource_type}_live", {})
    user_data = load_json(f"resources/{resource_type}.json")
    master_data = load_json(f"resources/{resource_type}_master.json")

    merged = master_data.copy()
    merged.update(user_data)
    merged.update(live)
    return merged

# --- CONFIG ---
st.set_page_config(page_title="Flowgent AI", layout="wide")
frameworks_all = load_resource("frameworks")

logo = load_logo()
if logo:
    st.image(logo, width=160)
else:
    st.markdown("### LOGO")

st.title("Ciao 👋 cosa vuoi fare oggi?")

with st.expander("⚙️ Impostazioni utente", expanded=False):
    show_settings()

# --- STEP 3: CARICA I FRAMEWORK ---
frameworks = load_resource("frameworks")


# --- FRAMEWORK SELEZIONABILI CON PRIORITÀ E MOSTRA TUTTI ---
st.subheader("✍️ Seleziona un framework di scrittura")
recommended_ids = ["tipps_coi", "tipps", "show_me_you_know_me", "challenger_framework", "bold_insight", "neat_email_structure"]
show_all = st.checkbox("🧠 Mostra tutti i framework", value=False)

if show_all:
    fw_dict = {fw["name"]: fw for fw in frameworks_all.values()}
else:
    fw_dict = {fw["name"]: fw for fw in frameworks_all.values() if fw["id"] in recommended_ids}

selected_fw_name = st.selectbox("Framework disponibile", list(fw_dict.keys()))
selected_fw = fw_dict[selected_fw_name]

structure = selected_fw.get("structure", selected_fw.get("rules", []))
st.markdown("📘 **Struttura del framework selezionato:**")
for i, step in enumerate(structure, 1):
    st.markdown(f"**{i}.** {step}")

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

    # ✅ Checkbox per invio al modello centrale
    send_to_admin = st.checkbox("🔄 Vuoi inviare questa buyer persona per migliorare il modello?")

    if st.button("💾 Salva Buyer Persona"):
        bp_data = load_all_buyer_personas()
        deep = st.session_state.get("deep_research", False)

    for role in [r.strip() for r in roles.split(",") if r.strip()]:
        if role not in bp_data:
            bp_data[role] = {"industries": {}}

        # Se mancano i pain/kpi → prova Deep Research
        pains = [pain_1, pain_2, pain_3]
        pains = [p for p in pains if p]
        kpis = ["[Da definire]"]

        if deep and not pains:
            context_text = value_prop + "\n" + (additional_notes or "")
            pain_auto, kpi_auto = generate_pain_kpi_from_context(role, "custom", context_text)
            if pain_auto:
                pains = pain_auto
            if kpi_auto:
                kpis = kpi_auto

        bp_data[role]["industries"]["custom"] = {
            "kpi": kpis,
            "pain": pains,
            "suggestion": value_prop
        }

    save_all_buyer_personas(bp_data)
    st.success("✅ Buyer Persona salvata!")


        # ✅ Log automatico se selezionato
        if send_to_admin:
            try:
                user_id = st.session_state.get("user_id", "anonimo")
                for role in [r.strip() for r in roles.split(",") if r.strip()]:
                    log_buyer_persona_submission(
                        user_id=user_id,
                        role=role,
                        industry="custom",
                        pain=[pain_1, pain_2, pain_3],
                        kpi=["[Da definire]"],
                        suggestion=value_prop
                    )
                st.success("📬 Inviata all’amministratore per valutazione.")
            except Exception as e:
                st.warning(f"❌ Errore nel log automatico: {e}")


  with st.expander("📂 Buyer Persona già salvate"):
    # Carica da user + master per distinguere origine
    custom_data = load_json("resources/buyer_personas.json")
    master_data = load_json("resources/buyer_personas_master.json")
    all_roles = sorted(set(custom_data.keys()) | set(master_data.keys()))

    # Aggiungi etichetta visiva per ogni ruolo
    display_roles = []
    for r in all_roles:
        if r in custom_data:
            display_roles.append(f"🟡 {r}")
        else:
            display_roles.append(f"🟢 {r}")

    # Mappa visualizzazione → ruolo reale
    role_map = {v: k for k, v in zip(all_roles, display_roles)}

    selected_display_role = st.selectbox("🧑‍💼 Scegli il ruolo", display_roles)
    selected_role = role_map[selected_display_role]

    # Carica i settori per il ruolo selezionato
    industries = sorted(
        list(
            set(
                master_data.get(selected_role, {}).get("industries", {}).keys()
            ).union(
                set(custom_data.get(selected_role, {}).get("industries", {}).keys())
            )
        )
    )

    selected_industry = st.selectbox("📂 Scegli il settore", industries)

    # Origine visiva (ufficiale vs personalizzata)
    origin = "🟡 Personalizzata" if selected_role in custom_data else "🟢 Ufficiale"
    st.markdown(f"**Origine della buyer persona selezionata:** {origin}")

    # Dati finali unificati (user override)
    full_data = master_data.get(selected_role, {}).copy()
    full_data.update(custom_data.get(selected_role, {}))

    selected_data = full_data.get("industries", {}).get(selected_industry)
    
    pain = selected_data.get("pain", [])
    kpi = selected_data.get("kpi", [])
    suggestion = selected_data.get("suggestion", "")

    st.markdown(f"- **Pain**: {', '.join(pain) if pain else '❌ Non definito'}")
    st.markdown(f"- **KPI**: {', '.join(kpi) if kpi else '❌ Non definito'}")
    st.markdown(f"- **Suggerimento**: {suggestion or '❌ Non definito'}")

    # 🔔 Mostra warning
    if not pain:
        st.warning("⚠️ Attenzione: il campo Pain è mancante.")
    if not kpi:
        st.warning("⚠️ Attenzione: il campo KPI è mancante.")
    if not suggestion:
        st.warning("⚠️ Attenzione: manca la value proposition.")
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
