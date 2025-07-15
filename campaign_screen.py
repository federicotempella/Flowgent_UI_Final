import streamlit as st
from utils import (
    parse_excel_file,
    parse_pdf_files,
    analyze_triggers_and_rank,
    generate_personalized_messages,
    save_to_library,
    load_all_buyer_personas
)
import pandas as pd
import io

st.subheader("🚀 Avvia una nuova campagna")

# 1. Caricamento Excel contatti
with st.expander("📁 1. Carica il file Excel contatti", expanded=True):
    uploaded_file = st.file_uploader("Seleziona il file Excel (.xlsx)", type=["xlsx"])
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
        total_size = sum([f.size for f in uploaded_pdfs]) / (1024 * 1024)
        if len(uploaded_pdfs) > 10:
            st.warning("⚠️ Hai caricato più di 10 PDF. Consigliato: max 10.")
        if total_size > 50:
            st.warning(f"⚠️ Dimensione totale: {total_size:.1f}MB.")
        st.success(f"📄 {len(uploaded_pdfs)} PDF caricati.")
        if st.button("📌 Memorizza questi PDF"):
            if "pdf_memory" not in st.session_state:
                st.session_state["pdf_memory"] = []
            st.session_state["pdf_memory"].extend(uploaded_pdfs)
            st.success("PDF aggiunti alla memoria temporanea.")

# Parsing PDF
pdfs_mem = st.session_state.get("pdf_memory", [])
parsed_pdf = st.session_state.get("parsed_pdf", {})
if pdfs_mem and st.button("🧠 Elabora PDF ora"):
    parsed_pdf = parse_pdf_files(pdfs_mem)
    st.session_state["parsed_pdf"] = parsed_pdf
    for filename, content in parsed_pdf.items():
        with st.expander(f"📄 {filename}", expanded=False):
            st.markdown("**Testo estratto (parziale):**")
            st.write(content[:1500] + "..." if len(content) > 1500 else content)

# Industry & ruolo
industry = st.selectbox("Scegli il settore", ["automotive", "fashion retail", "CPG", "tier 1 automotive"])
buyer_personas = load_all_buyer_personas()
roles = list(buyer_personas.keys())
selected_role = st.selectbox("🎯 Seleziona un ruolo", roles)
st.markdown("### 💬 Chatta con l’AI per arricchire il contesto (facoltativo ma potente)")
user_prompt = st.text_area("Scrivi qui una domanda, carica contenuti o chiedi aiuto...", key="campaign_chat")

if st.button("✉️ Invia alla chat AI"):
    if user_prompt:
        with st.spinner("💬 Elaborazione in corso…"):
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
            )
            ai_notes = response.choices[0].message.content
            st.markdown("**🧠 Risposta AI:**")
            st.write(ai_notes)
            st.session_state["ai_notes"] = ai_notes
    else:
        st.warning("Scrivi qualcosa prima di inviare.")

# Recupera anche le note AI (manual_input) dalla sessione
manual_input = st.session_state.get("ai_notes", "")

# Ranking & KPI
if st.button("📊 Mostra ranking & matrice KPI"):
    df = st.session_state.get("excel_df")
    if df is not None:
        ranked_df = analyze_triggers_and_rank(df, parsed_pdf, manual_input, buyer_personas)
        if not ranked_df.empty:
            st.subheader("🔎 Trigger → KPI → Messaggio suggerito")
            st.dataframe(ranked_df)
            st.session_state["ranked_df"] = ranked_df
            st.success("✔️ Analisi completata.")
        else:
            st.info("Nessun trigger noto trovato.")
    else:
        st.warning("Carica prima un file Excel.")

# --- Step: Genera messaggi personalizzati ---
if st.button("🧠 Genera messaggi personalizzati"):
    df = st.session_state.get("ranked_df")
    if df is not None:
        with st.spinner("🔄 Generazione messaggi in corso..."):
            selected_framework = st.selectbox("📐 Scegli un framework", ["Auto (da score)", "TIPPS", "TIPPS + COI", "Poke the Bear", "Harris NEAT"])
            output_df = generate_personalized_messages(df, framework_override=selected_framework)
            st.session_state["personalized_messages"] = output_df
            st.success("✔️ Messaggi generati con successo!")

# --- Step: Visualizza e modifica messaggi ---
output_df = st.session_state.get("personalized_messages")
if output_df is not None:
    st.subheader("📩 Messaggi personalizzati")
    for i, row in output_df.iterrows():
        st.markdown(f"##### 🎯 [{row['Nome']} – {row['Azienda']} – {row['Ruolo']}]")
        new_msg = st.text_area(f"✏️ Modifica messaggio", value=row['Messaggio generato'], key=f"msg_edit_{i}")
        output_df.at[i, "Messaggio generato"] = new_msg

    # Scarica Excel aggiornato
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        output_df.to_excel(writer, index=False, sheet_name="Messaggi")
    st.download_button("📥 Scarica messaggi", data=buffer.getvalue(), file_name="messaggi_personalizzati.xlsx")

    # Salva in libreria
    if st.button("💾 Salva tutti in libreria"):
        for _, row in output_df.iterrows():
            save_to_library("Messaggio personalizzato", row["Messaggio generato"])
        st.success("📚 Messaggi salvati nella libreria!")

# --- Step-critical GPT chat ---
st.markdown("### 🤖 Chatta con l’assistente AI sui messaggi")
user_prompt = st.text_area("Hai domande o vuoi modificarli con GPT?", key="chat_prompt_messages")

if st.button("✉️ Invia alla chat AI", key="send_chat_prompt_messages"):
    if user_prompt:
        with st.spinner("💬 Risposta AI in corso..."):
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.6,
            )
            st.markdown("**Risposta AI:**")
            st.write(response.choices[0].message.content)
    else:
        st.warning("Scrivi qualcosa prima di inviare.")
