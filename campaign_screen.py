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

# Genera messaggi
if st.button("🧠 Genera messaggi personalizzati"):
    df = st.session_state.get("excel_df")
    if df is not None:
        output_df = generate_personalized_messages(df)
        st.session_state["personalized_messages"] = output_df
        st.subheader("📩 Messaggi generati")
        st.dataframe(output_df)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            output_df.to_excel(writer, index=False, sheet_name="Messaggi")
        st.download_button(
            label="📥 Scarica messaggi in Excel",
            data=buffer.getvalue(),
            file_name="messaggi_personalizzati.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        if st.button("💾 Salva tutti nella libreria"):
            for _, row in output_df.iterrows():
                msg = f"{row['Messaggio generato']}"
                tipo = "Messaggio personalizzato"
                save_to_library(tipo, msg)
            st.success("✅ Salvati nella libreria.")
    else:
        st.warning("Carica prima un file Excel.")
