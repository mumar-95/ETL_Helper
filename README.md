# ETL Helper — Advanced Scenario Question Bank

Scenario-first Informatica interview preparation for **PowerCenter**, **IICS / CDI**, and **SQL (Oracle & SQL Server)**.

The platform ships a **pre-authored bank of 1,000+** practical scenarios with mandatory **A–M** explanations, interactive workbench actions, scenario-scoped chat, experience-based difficulty, and an AI expansion / verification workflow.

## Features

- 1,000 scenarios: PowerCenter 400 · IICS 350 · SQL 250
- Categories spanning mapping design, lookups, SCD, incremental loads, performance, recovery, architecture, and more
- Full **A–M** explanation engine (business → sample data → implementation → alternatives → interview answer → follow-ups)
- Workbench actions: **Solve**, **Explain Step by Step**, **Show SQL / Mapping Logic**, **Ask Follow-up Questions**
- Conversational follow-ups bound to the selected scenario (Groq)
- Experience-band difficulty adaptation
- Continuous expansion admin with dedup, review queue, and labels (`verified`, `publicly_reported`, `community`, `ai_generated`)

## Setup

```powershell
cd "ETL_Helper"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env and set GROQ_API_KEY (needed for chat + optional Groq expansion)
```

Optional Streamlit secrets:

```powershell
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

## Populate the 1,000-scenario bank

```powershell
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\generate_bank.py
.\.venv\Scripts\python.exe scripts\validate_bank.py
```

`generate_bank.py` uses the local deterministic A–M author so the full bank can be built offline and reproducibly. Expansion Admin can still generate additional scenarios via Groq.

## Run the app

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

## Project layout

See `src/` for taxonomy, SQLite repositories, prompts, and services. Streamlit pages live under `pages/`. Offline scripts live under `scripts/`.

## Quality labels

| Label | Meaning |
|---|---|
| `verified` | Structurally reviewed / curated technical scenario |
| `publicly_reported` | Reported as a real interview pattern (still not a company claim unless sourced) |
| `community` | Community-reported practice scenario |
| `ai_generated` | AI practice scenario — **never** presented as company-asked |

## License

Apache License 2.0 — see `LICENSE`.
