from openai import OpenAI

client = OpenAI(api_key="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")

# Clé API OpenAI (assurez-vous de la garder privée)

# Fonction pour valider des noms avec GPT
def validate_name_with_gpt(name):
    prompt = f"Validez si le nom '{name}' est bien formaté (uniquement lettres et espaces). Répondez par 'Valide' ou 'Non valide'."
    response = client.completions.create(engine="text-davinci-003",
    prompt=prompt,
    max_tokens=10)
    return response.choices[0].text.strip()

# Exemple d'utilisation
name = "Jean Dupont"
validation = validate_name_with_gpt(name)
print(f"Résultat pour '{name}': {validation}")
