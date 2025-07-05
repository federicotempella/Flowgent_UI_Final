# Flowgent UI - Sales Assistant Streamlit App

Questa app Streamlit consente di:
- ✅ Avviare campagne di contatto con parsing avanzato del file Excel
- 🤖 Simulare conversazioni AI con logica Assistant centralizzato
- 🎯 Analizzare trigger multipli per contatto (con validazione)
- 📊 Visualizzare report/log da Google Sheet
- 📚 Salvare contenuti personalizzati in libreria personale
- ✉️ Gestire feedback, aggiornamenti, privacy e impostazioni utente

---

## ✅ Requisiti
- Python **3.10**
- Streamlit
- `openai`
- `gspread`, `oauth2client`

---

## ⚙️ Configurazione Segreti (Streamlit → Settings → Secrets)

```toml
OPENAI_API_KEY = "sk-..."
ASSISTANT_ID = "asst_..."
GOOGLE_SHEET_ID = "ID-del-foglio-Google"

SERVICE_ACCOUNT_JSON =