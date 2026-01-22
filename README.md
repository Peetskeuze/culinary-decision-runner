# Peet Kiest / Peet Card

Peet Kiest is een AI-gedreven maaltijdkeuze-app.
Het project is opgezet rond stabiliteit, herhaalbaarheid en expliciete keuzes,
niet rond maximale creativiteit of variatie.

Deze repository bevat zowel de engine als meerdere Streamlit-apps
die verschillende user flows ondersteunen (vandaag vs vooruit).

---

## Wat dit project wél is
- Een keuze-engine voor “wat eten we”
- Deterministisch: dezelfde input → dezelfde structuur output
- Context-gedreven (today vs forward)
- Gericht op rust in UX en voorspelbaar gedrag
- Geschikt voor PDF-output en externe launchers (Carrd)

## Wat dit project níet is
- Geen receptengenerator
- Geen chatbot
- Geen zelflerend systeem
- Geen UI-gedreven logica
- Geen plek voor impliciete aannames

---

## Architectuuroverzicht

### Centrale engine
Alle logica zit in:

