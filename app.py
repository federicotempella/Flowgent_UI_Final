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
    with st.expander("🧠 Potenzia la tua proposta"):
        col1, col2 = st.columns(2)
        if col1.button("🔎 Cerca sul web", key="web_value_prop"):
            st.session_state["web_value_prop"] = perform_web_search(value_prop)
            st.info("🔗 Risultato della ricerca web:")
            st.markdown(st.session_state["web_value_prop"])
        if col2.button("🧠 Deep Research", key="deep_value_prop"):
            st.session_state["deep_value_prop"] = perform_deep_research(value_prop)
            st.info("📌 Insight da deep research:")
            st.markdown(st.session_state["deep_value_prop"])


    st.markdown("#### 2️⃣ Quali sono i 3 pain point principali che risolvi?")
    pain_1 = st.text_input("Pain Point 1")
    pain_2 = st.text_input("Pain Point 2")
    pain_3 = st.text_input("Pain Point 3")

    st.markdown("#### 3️⃣ Per quali ruoli vuoi creare la matrice?")
    roles = st.text_input("Ruoli (separati da virgola)", placeholder="Es: CIO, Supply Chain Manager, EDI Manager")

    st.markdown("#### 📎 Vuoi caricare risorse extra?")
    uploaded_file = st.file_uploader("Carica PDF o Excel (opzionale)", type=["pdf", "xlsx"])
    additional_notes = st.text_area("Note aggiuntive (facoltative)")
    with st.expander("🧠 Approfondisci le note"):
        col1, col2 = st.columns(2)
        if col1.button("🔎 Cerca sul web", key="web_notes"):
            st.session_state["web_notes"] = perform_web_search(additional_notes)
            st.info("🔗 Risultato della ricerca web:")
            st.markdown(st.session_state["web_notes"])
        if col2.button("🧠 Deep Research", key="deep_notes"):
            st.session_state["deep_notes"] = perform_deep_research(additional_notes)
            st.info("📌 Insight da deep research:")
            st.markdown(st.session_state["deep_notes"])


    # ✅ Checkbox per invio al modello centrale
    send_to_admin = st.checkbox("🔄 Vuoi inviare questa buyer persona per migliorare il modello?")

   if st.button("💾 Salva Buyer Persona"):
    bp_data = load_all_buyer_personas()
    deep = st.session_state.get("deep_research", False)
    new_entries = {}
    preview_roles = []

    # 🔍 SUGGERIMENTO RUOLI SIMILI
    from difflib import get_close_matches
    similar_roles = []
    existing_roles = list(bp_data.keys())

    for role in [r.strip() for r in roles.split(",") if r.strip()]:
        if role not in bp_data:
            match = get_close_matches(role, existing_roles, n=1, cutoff=0.6)
            if match:
                similar_roles.append((role, match[0]))

    if similar_roles:
        st.info("📚 Abbiamo trovato dei ruoli simili già presenti. Vuoi usarli come base?")
        for input_role, suggested_role in similar_roles:
            if st.button(f"📋 Copia da {suggested_role} per {input_role}"):
                source_data = bp_data[suggested_role]
                new_entries[input_role] = {
                    "kpi": source_data["industries"].get("custom", {}).get("kpi", ["[Da definire]"]),
                    "pain": source_data["industries"].get("custom", {}).get("pain", ["[Da definire]"]),
                    "suggestion": value_prop
                }
                st.success(f"✅ Importato da {suggested_role} per {input_role}")

    # 🧠 GENERAZIONE NUOVE ENTRY
    for role in [r.strip() for r in roles.split(",") if r.strip()]:
        if role not in bp_data:
            bp_data[role] = {"industries": {}}

        pains = [pain_1, pain_2, pain_3]
        pains = [p for p in pains if p]
        kpis = ["[Da definire]"]
        auto_generated = False

        if deep and not pains:
            context_text = value_prop + "\n" + (additional_notes or "")
            pain_auto, kpi_auto = generate_pain_kpi_from_context(role, "custom", context_text)

            if pain_auto:
                st.warning(f"⚠️ Pain point generati automaticamente per {role}:")
                for i, p in enumerate(pain_auto, 1):
                    pain_auto[i-1] = st.text_input(f"Pain auto {i}", value=p, key=f"pain_auto_{i}_{role}")
                pains = pain_auto
                auto_generated = True

            if kpi_auto:
                st.warning(f"⚠️ KPI generati automaticamente per {role}:")
                for i, k in enumerate(kpi_auto, 1):
                    kpi_auto[i-1] = st.text_input(f"KPI auto {i}", value=k, key=f"kpi_auto_{i}_{role}")
                kpis = kpi_auto
                auto_generated = True

        new_entries[role] = {
            "kpi": kpis,
            "pain": pains,
            "suggestion": value_prop
        }
        preview_roles.append(role)

        # ✅ Merge con esistenti e salvataggio permanente
        for role in preview_roles:
            if role not in bp_data:
                bp_data[role] = {"industries": {}}
            bp_data[role]["industries"]["custom"] = new_entries[role]

        # ✅ Salva nel file JSON dell'utente
        save_all_buyer_personas(bp_data)
        st.success("✅ Buyer Persona salvate e subito integrate nel modello.")
       
    # ⚠️ FALLBACK se KPI o Pain mancanti
    validation_errors = []
    for role, data in new_entries.items():
        if not data["pain"] or all(p.strip() == "" for p in data["pain"]):
            validation_errors.append(f"Pain mancante per il ruolo {role}")
        if not data["kpi"] or all(k.strip() == "" or k.strip() == "[Da definire]" for k in data["kpi"]):
            validation_errors.append(f"KPI mancante per il ruolo {role}")

    if validation_errors:
        st.warning("⚠️ Alcuni dati sembrano incompleti. Puoi modificarli manualmente oppure completare con AI.")
        for err in validation_errors:
            st.markdown(f"- {err}")

        if st.button("💡 Completa automaticamente i campi mancanti con GPT"):
            for role, data in new_entries.items():
                if not data["pain"] or all(p.strip() == "" for p in data["pain"]):
                    context_text = value_prop + "\n" + (additional_notes or "")
                    pains_gpt, _ = generate_pain_kpi_from_context(role, "custom", context_text)
                    if pains_gpt:
                        st.info(f"Pain generati per {role}: {pains_gpt}")
                        data["pain"] = pains_gpt
                if not data["kpi"] or all(k.strip() == "" or k.strip() == "[Da definire]" for k in data["kpi"]):
                    _, kpis_gpt = generate_pain_kpi_from_context(role, "custom", context_text)
                    if kpis_gpt:
                        st.info(f"KPI generati per {role}: {kpis_gpt}")
                        data["kpi"] = kpis_gpt


        # 👁️ Mostra anteprima
        st.markdown("### 👁️ Preview della Buyer Persona prima del salvataggio:")
        for role in preview_roles:
            data = new_entries[role]
            st.markdown(f"#### 👤 {role}")
            st.markdown(f"- **Pain Point**: {', '.join(data['pain'])}")
            st.markdown(f"- **KPI**: {', '.join(data['kpi'])}")
            st.markdown(f"- **Value Proposition**: {data['suggestion']}")

        # Conferma salvataggio
        confirm_save = st.checkbox("✅ Confermo e voglio salvare queste Buyer Persona")

        # ⚠️ Validazione logica pre-salvataggio
        validation_errors = []

        for role, data in new_entries.items():
            if not data["pain"] or any(p.strip() == "" for p in data["pain"]):
                validation_errors.append(f"🔴 Il ruolo **{role}** non ha pain point definiti.")
            if not data["kpi"] or any(k.strip() == "" or k.strip() == "[Da definire]" for k in data["kpi"]):
            validation_errors.append(f"🟠 Il ruolo **{role}** ha KPI mancanti o non definiti.")

        if validation_errors:
            st.warning("⚠️ Alcuni dati sembrano incompleti. Puoi modificarli manualmente oppure completare con AI.")
            for err in validation_errors:
                st.markdown(f"- {err}")

        if st.button("💡 Completa automaticamente i campi mancanti con GPT"):
            for role, data in new_entries.items():
                if not data["pain"] or all(p.strip() == "" for p in data["pain"]):
                    context_text = value_prop + "\n" + (additional_notes or "")
                    pains_gpt, _ = generate_pain_kpi_from_context(role, "custom", context_text)
                    if pains_gpt:
                        st.info(f"Pain generati per {role}: {pains_gpt}")
                        data["pain"] = pains_gpt
                if not data["kpi"] or all(k.strip() == "" or k.strip() == "[Da definire]" for k in data["kpi"]):
                    _, kpis_gpt = generate_pain_kpi_from_context(role, "custom", context_text)
                    if kpis_gpt:
                        st.info(f"KPI generati per {role}: {kpis_gpt}")
                        data["kpi"] = kpis_gpt

        if confirm_save:
            for role in new_entries:
                bp_data[role]["industries"]["custom"] = new_entries[role]
            save_all_buyer_personas(bp_data)
            st.success("✅ Buyer Persona salvata!")

            # 📨 Deep Research → invio all’admin
            if deep:
                send_to_admin = st.checkbox("📤 Vuoi inviare questa buyer persona all’admin per migliorare il modello globale?")
                if send_to_admin:
                    try:
                        user_id = st.session_state.get("user_id", "anonimo")
                        for role in new_entries:
                            log_buyer_persona_submission(
                                user_id=user_id,
                                role=role,
                                industry="custom",
                                pain=new_entries[role]["pain"],
                                kpi=new_entries[role]["kpi"],
                                suggestion=new_entries[role]["suggestion"]
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
    st.subheader("🤖 Simulatore GPT")
    user_input = st.text_area("Scrivi un prompt...")
    if user_input:
         # Espandi opzioni di ricerca e approfondimento
        with st.expander("🧠 Stimola l’analisi GPT"):
            col1, col2 = st.columns(2)
            if col1.button("🔎 Cerca sul web", key="web_user_input"):
                st.session_state["web_user_input"] = perform_web_search(user_input)
                st.info("🔗 Risultato della ricerca web:")
                st.markdown(st.session_state["web_user_input"])
            if col2.button("🧠 Deep Research", key="deep_user_input"):
                st.session_state["deep_user_input"] = perform_deep_research(user_input)
                st.info("📌 Insight da deep research:")
                st.markdown(st.session_state["deep_user_input"])

elif action == "linkedin_post":
    st.subheader("📝 Generatore di Post LinkedIn")
    idea = st.text_input("Idea o tema del post:")
    if idea:
        with st.expander("🧠 Arricchisci l’idea del post"):
            col1, col2 = st.columns(2)
            if col1.button("🔎 Cerca sul web", key="web_post_idea"):
                st.session_state["web_post_idea"] = perform_web_search(idea)
                st.info("🔗 Risultato della ricerca web:")
                st.markdown(st.session_state["web_post_idea"])
            if col2.button("🧠 Deep Research", key="deep_post_idea"):
                st.session_state["deep_post_idea"] = perform_deep_research(idea)
                st.info("📌 Insight da deep research:")
                st.markdown(st.session_state["deep_post_idea"])
        
        # Scelta del tono e generazione del post
        tone = st.selectbox("Tono", ["Professionale", "Informale", "Provocatorio"])
        if st.button("Genera post"):
            # Chiamata GPT per generare il contenuto del post con il tono scelto
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"Genera un post LinkedIn in tono {tone}."},
                    {"role": "user", "content": idea}
                ],
                temperature=0.8,
            )
            post = response.choices[0].message.content.strip()
            st.text_area("Post generato", post, height=200)
            if st.button("💾 Salva in libreria"):
                save_to_library("Post LinkedIn", post)
                st.success("✅ Post salvato nella tua libreria.")
    else:
        st.info("Inserisci un'idea per generare il post.")


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
