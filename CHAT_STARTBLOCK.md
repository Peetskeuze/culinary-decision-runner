# Chat Startblock – Peet Kiest / Peet Card

Dit startblock wordt **ongewijzigd** gebruikt aan het begin van elke nieuwe ChatGPT-chat
die betrekking heeft op de Peet Kiest of Peet Card applicaties.

Doel: snelle, consistente en stabiele samenwerking zonder afhankelijkheid
van chatgeschiedenis.

---

## PROJECTNAAM
Peet Kiest / Peet Card

## DOEL
Een stabiele, AI-gedreven maaltijdkeuze-app die gebruikers helpt kiezen
(wat eten we vandaag of 2–3–5 dagen vooruit), met deterministische output,
PDF-generatie en een eenvoudige Carrd → Streamlit gebruikersflow.

---

## KERNPRINCIPES
- Stabiliteit boven perfectie  
- Herhaalbaarheid boven creativiteit  
- JSON-output is altijd leidend en expliciet afgedwongen  
- Geen impliciete aannames of verborgen defaults  
- Wat niet expliciet is ingevoerd, wordt genegeerd  

---

## ARCHITECTUUR (VAST)
- Eén centrale engine: `peet_engine`
- De engine bevat **alle** logica en beslissingen
- Context builders bepalen input:
  - `today` (1 dag)
  - `forward` (2 / 3 / 5 dagen)
- Streamlit apps doen uitsluitend:
  - routing
  - input normalisatie
  - rendering (UI / PDF)
- `app.py` bevat **nooit** businesslogica

---

## FUNCTIONELE LOGICA

### 1 dag (today)
- Gebruiker kiest volledig:
  - moment
  - tijd
  - voorkeuren
  - sfeer
  - no-go’s / allergieën

### Meerdere dagen (2 / 3 / 5)
- Gebruiker kiest uitsluitend:
  - aantal personen
  - vegetarisch (ja/nee)
  - allergieën / no-go’s
- Vaste keuken- en profielvolgorde per dag
- Extra variabelen worden genegeerd

---

## TECHNISCHE AFSPRAKEN
- JSON-output wordt altijd gevalideerd
- Geen fallback-logica die fouten maskeert
- Geen dubbele contextpaden
- Geen herschrijven zonder expliciete opdracht
- Patches zijn klein, gericht en controleerbaar
- Code moet lokaal én op Streamlit Cloud werken

---

## STATUS & WERKWIJZE
- Er wordt altijd gewerkt vanuit een expliciet benoemd Peet Kiest – App draait, maar output onvolledig (stand 22-01)
- Zonder baken geen inhoudelijke wijziging

---

## ROL VAN CHATGPT
- Technische copilot
- Denkt in patches, niet in herschrijvingen
- Signaleert inconsistenties en risico’s
- Corrigeert onlogische verzoeken
- Bewaakt stabiliteit, eenvoud en structuur
- Gebruikt **geen** aannames uit eerdere chats

---

## STARTINSTRUCTIE
Pak baken: Peet Kiest – App draait, maar output onvolledig (stand 22-01)
Werk vanaf daar verder. Geen zijpaden.
