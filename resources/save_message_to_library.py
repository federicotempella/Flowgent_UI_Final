import json
import os
from datetime import datetime

def save_message_to_library(
    nome,
    azienda,
    ruolo,
    framework,
    trigger,
    messaggio,
    note_deep,
    file_path="resources/messages_library.json"
):
    # Assicura che la directory esista
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Nuovo messaggio da salvare
    new_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "nome": nome,
        "azienda": azienda,
        "ruolo": ruolo,
        "framework": framework,
        "trigger": trigger,
        "messaggio": messaggio,
        "note_deep": note_deep
    }

    # Se il file esiste, carica il contenuto attuale
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Aggiungi il nuovo messaggio
    data.append(new_entry)

    # Salva tutto nel file
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"✅ Messaggio salvato in {file_path}")
