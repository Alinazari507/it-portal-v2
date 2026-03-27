# IT Service Portal – RapidRoute

**Version:** 2.0  
**Lernfeld:** LF 6.3 – Prozessgestaltung und Dienstleistungsstruktur  
**Szenario:** RapidRoute Logistics GmbH (Quick‑Commerce‑Startup)

## 📖 Projektbeschreibung

Dieses **IT‑Service‑Portal** ist eine webbasierte Anwendung zur professionellen Verwaltung von IT‑Dienstleistungen nach **ITIL 4** und **ITAM** (IT‑Asset‑Management).  
Es wurde im Rahmen des Lernfelds 6.3 entwickelt und bildet den gesamten Lebenszyklus einer IT‑Ressource ab – von der strategischen Planung über den täglichen Support bis zur sicheren Aussonderung.

**Ziel:** Schaffung eines automatisierten, messbaren und kundenorientierten IT‑Service‑Managements für das Wachstumsunternehmen RapidRoute.

---

## ✨ Hauptfunktionen

### 🧭 Service‑Katalog (Business‑ & Technik‑Sicht)
- Zweistufiger Katalog: einfache Business‑Beschreibungen für Endanwender, detaillierte technische Beschreibungen für IT‑Mitarbeiter.
- Kategorien: Hardware, Software, Zugang & Berechtigungen, Support.
- Selbstbedienungs‑Portal mit „One‑Click‑Request“.

### ⚙️ Automatisierte Prozesse
- **Priorisierung:** Automatische Berechnung der Ticket‑Priorität (P1–P4) basierend auf Service‑Kategorie und Begründung.
- **SLA‑Management:** Hinterlegte Service‑Level‑Agreements (SLA) mit individuellen Reaktions‑ und Lösungszeiten. Überschreitungen werden im Dashboard farblich markiert.
- **Request Fulfillment:** Workflow‑Unterstützung für Genehmigungen, Lagerprüfung und Bestellauslösung.

### 🖥️ CMDB (Configuration Management Database)
- Zentrale Inventarverwaltung aller IT‑Assets (Laptops, Monitore, Docking‑Stations, …).
- IMAC/RD‑Unterstützung: **I**nstall, **M**ove, **A**dd, **C**hange, **R**emove, **D**isposal werden automatisch in einem Log protokolliert.
- Statusverwaltung: „Im Lager“, „Zugewiesen“, „Defekt“, „Ausgemustert“.
- DSGVO‑konforme Datenlöschung und Löschprotokolle.

### 📊 Metriken & Vereinbarungen
- **SLAs:** für jede Priorität definierte Reaktions‑ und Lösungszeiten.
- **OLAs:** interne Vereinbarungen zwischen 1st‑, 2nd‑ und 3rd‑Level‑Support.
- **SLIs & KPIs:** z. B. MTTR, SLA‑Compliance, User Satisfaction Score.
- **Reporting:** Excel‑Export aller Tickets mit umfangreichen Statistiken.

### 📚 Known Error Database (KEDB)
- Speicherung von Fehlercodes, Beschreibungen, Workarounds und endgültigen Lösungen.
- Hilft bei schnellerer Störungsbehebung (Incident Management).

### 👥 Rollen & Berechtigungen
- **Benutzer:** Können Services anfordern, eigene Anfragen einsehen und den Status verfolgen.
- **Administratoren:** Verwalten den Service‑Katalog, die CMDB, die KEDB und alle eingehenden Tickets. Änderungen an Ticket‑Status, Inventar und Fehlern sind möglich.

---

## 🛠️ Technologie‑Stack

| Bereich         | Technologie                     |
|-----------------|---------------------------------|
| Backend         | Python 3, Flask, Flask‑Login    |
| Datenbank       | SQLite3                         |
| Frontend        | HTML5, CSS3, Bootstrap (optional)|
| Export          | pandas, openpyxl (Excel‑Export) |
| Entwicklung     | Virtual Environment (venv)      |

---

## 🚀 Installation & Start

### 1. Repository klonen
```bash
git clone https://github.com/Alinazari507/it-portal-v2.git
cd it-portal-v2