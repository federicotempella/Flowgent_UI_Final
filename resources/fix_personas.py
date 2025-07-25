import json

# Percorso file
path = "resources/buyer_personas.json"

# Carica file esistente
with open(path, "r", encoding="utf-8") as f:
    personas = json.load(f)

# Aggiorna se mancano i campi
for persona in personas:
    if "symptom" not in persona:
        persona["symptom"] = []
    if "damage" not in persona:
        persona["damage"] = []

# Salva di nuovo
with open(path, "w", encoding="utf-8") as f:
    json.dump(personas, f, indent=2, ensure_ascii=False)

print("✅ File aggiornato con symptom e damage se mancanti.")
