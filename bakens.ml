# Bakens – Peet Kiest / Peet Card

Dit document beschrijft alle vastgelegde mijlpalen (“bakens”)
in de ontwikkeling van Peet Kiest en Peet Card.

Een baken markeert een stabiele toestand.
Aanpassing van een baken gebeurt alleen met expliciete opdracht.

---

## 📌 BAKEN 1
### Naam
Peet Engine – Structuur staat & parsing.py gevuld

### Status
Afgerond (stabiel referentiepunt)

### Betekenis
- Mappenstructuur van `peet_engine` is vastgesteld
- parsing helpers aanwezig (`safe_int`, normalisatie, lists)
- Basis gelegd voor context-gedreven engine

---

## 📌 BAKEN 2
### Naam
Peet Engine – Bereiding & Runner schoon

### Status
Afgerond

### Betekenis
- Engine runner opgeschoond
- Profiel-specifieke bereidingsintentie vastgelegd
- Responses API stabiel geïntegreerd
- Geen UI-afhankelijkheden in engine

---

## 📌 BAKEN 3
### Naam
Peet-Card – Context-splitsing definitief

### Status
Afgerond (kritisch)

### Betekenis
- Eén engine, twee expliciete context builders:
  - today
  - forward
- 1 dag = volledige invoer
- 2 / 3 / 5 dagen = minimale invoer
- UX-beperkingen worden vóór engine afgedwongen

---

## 📌 BAKEN 4
### Naam
Peet-Card – Vooruit-keuzelogica definitief

### Status
Afgerond

### Betekenis
- Vaste keukenvolgorde per vooruit-dag
- Geen variabele keukenkeuze bij multi-day
- Context bepaalt gedrag, niet UI

---

## 📌 BAKEN 5
### Naam
JSON-afdwinging hersteld

### Status
Afgerond (stabiliteitsbaken)

### Betekenis
- JSON wordt altijd expliciet afgedwongen
- Geen vrije tekst meer uit het model
- Fouten leiden tot zichtbare errors, niet stille fallbacks

---

## 📌 BAKEN 6
### Naam
Carrd → Streamlit flow stabiel (Vooruit)

### Status
Afgerond

### Betekenis
- Carrd levert parameters via GET
- Streamlit start direct met spinner
- Meerdere dagen renderen correct
- PDF-download onderaan beschikbaar

---

## 📌 BAKEN 7
### Naam
Opruimfase 0.5 afgerond

### Status
Afgerond

### Betekenis
- Overbodige scripts gedepricate
- Runtime-kritische bestanden geïdentificeerd
- Structuur opgeschoond zonder regressies

---

## 🧭 ACTIEF BAKEN
👉 **Hier benoem je het baken waar je momenteel op werkt**

Voorbeeld:
- *Actief baken: Peet-Card – app.py schoon trekken & één contextpad afdwingen*

---

## 🔒 REGELS
- Een baken wordt niet “stil” aangepast
- Nieuwe ideeën = nieuw baken
- Bugs fixen binnen een baken mag
- Architectuur wijzigen = altijd nieuw baken
2026-01-26 – Carrd Form Mobile Layout & Typography stabiel

- Form past exact op één mobiel scherm
- Uitlijning links strak en consistent
- Witruimte gelijkgetrokken via Container Mobile padding
- Tekst opgeschaald via Form Fields Mobile size (±1.2)
- Rustige app-achtige look bereikt

