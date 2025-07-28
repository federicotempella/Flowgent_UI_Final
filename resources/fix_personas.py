import json

# Percorso file
path = "resources/buyer_personas.json"

# Carica file esistente
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Correzione campi mancanti in ogni industry
for ruolo, role_data in data.items():
    industries = role_data.get("industries", {})
    for industry, industry_data in industries.items():
        if "symptom" not in industry_data:
            industry_data["symptom"] = []
        if "damage" not in industry_data:
            industry_data["damage"] = []

# Salva il file aggiornato
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ File aggiornato correttamente con symptom e damage.")

