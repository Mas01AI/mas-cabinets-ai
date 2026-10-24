# Mas Cabinets AI Agent

An AI-assisted lead-generation and follow-up agent for **MAS Remodeling and
Construction LLC (aka Mas Cabinets)** — custom cabinetry and remodeling in
Apopka / Orlando and Central Florida.

This repository is the real Mas Cabinets agent codebase. It replaces the
previous contents of this repo (a copy of third-party documentation that
contained no Mas Cabinets code).

## What the agent does

1. **Intake** — loads leads (from a JSON file today; website forms and ad
   platforms can feed the same format).
2. **Scoring** — scores every lead 0–100:
   - Florida focus-area check (Apopka/Orlando + Lake, Orange, Osceola, Polk
     and Seminole counties). Out-of-area leads are flagged, not discarded.
   - Service match against the services Mas actually offers.
   - Urgency and budget signals from the lead's timeline and message.
   - Contact completeness (name / email / phone) — can we actually reach them?
3. **Follow-up drafts** — generates a same-day follow-up email draft for each
   lead from the business work email, offering a **free consultation and free
   estimate**.
4. **HubSpot push (optional)** — creates/searches contacts, creates deals and
   logs notes in the HubSpot portal **"MAS Remodeling and Construction"**
   (portal ID 247703427) via the HubSpot CRM API.

Without a HubSpot token the agent runs in **dry-run mode**: everything works
end-to-end, nothing is sent anywhere, and the HubSpot step prints exactly what
it *would* do.

## Business profile (baked into `src/mas_agent/config.py`)

| | |
|---|---|
| Business | MAS Remodeling and Construction LLC, aka Mas Cabinets |
| Address | 535 Cooper Commerce Dr Ste 380, Apopka, FL 32703 |
| Phone | (631) 710-1202 |
| Website | mascabinets.com |
| Work email | mseeriram@aol.com |
| Hours | Mon–Fri 8am–5pm, Sat 8am–2pm, Sun closed |
| Services | Custom kitchen cabinets, bathroom vanities, custom closets, built-in storage, kitchen remodeling, general contracting |
| Edge | CAD design + CNC precision fabrication |
| Offer | Free consultation and free estimate |
| Focus area | Florida only: Apopka/Orlando + Lake, Orange, Osceola, Polk, Seminole counties |

## Setup

Requires **Python 3.10+**. No third-party packages — standard library only.

```bash
git clone https://github.com/Mas01AI/mas-cabinets-ai.git
cd mas-cabinets-ai
cp .env.example .env   # then fill in what you have; all values are optional
```

## Configuration (environment variables)

| Variable | Required | Purpose |
|---|---|---|
| `HUBSPOT_ACCESS_TOKEN` | No | HubSpot private-app access token. Without it, HubSpot runs in dry-run mode. |
| `WORK_EMAIL` | No | Sender address for follow-up drafts. Defaults to `mseeriram@aol.com`. |
| `OPENAI_API_KEY` | No | Reserved for future AI message personalisation. Not used by the current stdlib pipeline. |
| `MAS_HUBSPOT_PORTAL_ID` | No | Defaults to `247703427`. |

Configuration is read from the process environment and, if present, from a
local `.env` file (never commit `.env` — it is gitignored).

## Run it

```bash
# Demo: score the sample leads, print follow-up drafts (dry-run)
PYTHONPATH=src python -m mas_agent demo

# Score any leads file (same JSON shape as data/sample_leads.json)
PYTHONPATH=src python -m mas_agent process path/to/leads.json

# Same, but actually push to HubSpot (needs HUBSPOT_ACCESS_TOKEN set)
PYTHONPATH=src python -m mas_agent process path/to/leads.json --push

# Just the business profile the agent is using
PYTHONPATH=src python -m mas_agent profile
```

## Tests

```bash
PYTHONPATH=src python tests/test_scoring.py   # plain python, no dependencies
# or, if pytest is installed:
PYTHONPATH=src python -m pytest tests/
```

## Project structure

```
.
├── README.md
├── .env.example          # config template — no real secrets, ever
├── .gitignore
├── data/
│   └── sample_leads.json # 3 sample leads (strong FL, FL bathroom, out-of-area NY)
├── src/
│   └── mas_agent/
│       ├── __init__.py
│       ├── __main__.py   # `python -m mas_agent`
│       ├── cli.py        # command-line interface / demo mode
│       ├── config.py     # env loading + baked-in business profile
│       ├── models.py     # Lead dataclass
│       ├── scoring.py    # lead scoring (area, service, urgency, contact)
│       ├── hubspot.py    # HubSpot CRM API client (urllib, dry-run safe)
│       ├── followup.py   # follow-up email draft templates
│       └── agent.py      # orchestration: intake -> score -> draft -> push
└── tests/
    └── test_scoring.py
```

## Roadmap

- Connect website / Google Business Profile / Meta lead forms as intake sources.
- Send follow-ups (with human approval) instead of only drafting them.
- Optional OpenAI-powered personalisation of the first follow-up message.
