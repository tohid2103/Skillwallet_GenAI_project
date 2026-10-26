# Multimodal Construction Intelligence Platform

Skill Wallet Capstone Project 1. A Streamlit app that combines Gemini vision analysis, rule-based project estimation and an AI engineering assistant for construction sites. It needs no database and deploys in one click on Streamlit Community Cloud.

## Features

| Module | What it does |
|---|---|
| **Safety & PPE Audit** | Upload a site photo. Gemini checks helmets, high-vis vests, steel-toe boots and harnesses against OSHA 1926 and IS 456 / NBC 2016 practice, and returns a safety score (0-100), overall status, PPE checklist and hazards with severity (Low, Medium, High, Critical) and remedies. Download the result as JSON. |
| **Crack Diagnostics** | Upload a concrete or wall photo. The app classifies the defect (Hairline, Settlement, Structural Shear, Thermal Expansion, Spalling) and gives estimated width in mm, root causes, repairs (epoxy injection, structural re-grouting) and urgency. |
| **Planning & Valuation** | Choose structure type, built-up area, location tier and completion percentage. The app calculates total budget, capex incurred, current asset valuation (INR in Lakhs/Crores), steel and cement requirements and milestone progress. It also builds a Pollinations AI prompt for a conceptual 3D rendering. |
| **Daily Site Assistant** | Pick the weather (Normal, High Wind, Heavy Rain, Extreme Heat) for dynamic safety alerts, then chat with a multi-turn construction engineering assistant. |

**Demo mode:** with no API key, every module returns sample output so the app can be explored offline. The sidebar shows a LIVE or DEMO badge. If a live call fails (bad key, quota, malformed JSON), the app falls back to demo output with a warning instead of crashing.

## Project structure

```
.
├── app.py            # entire application
├── requirements.txt
└── README.md
```

## Run locally

Requires Python 3.9 or newer.

**Windows (PowerShell)**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once. If `streamlit` is not recognised, use `python -m streamlit run app.py`.

## Gemini API key

1. Create a key in [Google AI Studio](https://aistudio.google.com/apikey).
2. Paste it into the sidebar field once the app is running.

The key is held in session memory only. It is never written to disk or logged. The model name is editable in the sidebar and defaults to `gemini-2.5-flash`.

## Deploy to Streamlit Community Cloud

1. Push `app.py`, `requirements.txt` and `README.md` to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and choose **New app**.
3. Select the repository and branch, and set **Main file path** to `app.py`.
4. Click **Deploy**.

Optional: to preconfigure a key for all visitors, add `GEMINI_API_KEY` under app **Settings > Secrets**. The current code reads the key from the sidebar field only, so wiring in `st.secrets` is a small change if you want it.

## Architecture

- **UI:** Streamlit with custom CSS (metric cards, status pills, alert banners, light and dark theme support)
- **Vision and chat:** `google-genai` SDK, Gemini multimodal calls with JSON response mode for structured reports
- **Estimator:** rule-based Indian cost model (per-sqft build and market rates by tier, structure multipliers, steel and cement thumb rules)
- **Renders:** Pollinations AI image URL built from the project inputs
- **State:** `st.session_state` only

## Estimation model

Valuation and material figures are indicative assumptions, not sourced market data.

- Budget = area × tier build rate × structure multiplier
- Current valuation = full market value × (35% land/approvals share + 65% × completion)
- Steel and cement come from per-sqft thumb rules per structure type

Tune the `STRUCT` and `TIER` dictionaries in `app.py` to match local rates.

## Limitations

- AI image analysis is a screening aid. It is not a substitute for a site safety officer or a licensed structural engineer, and crack width from a photo is approximate.
- Estimates should be checked by a quantity surveyor and against local registry rates.
- The Pollinations service is free and external, so it can be slow or unavailable.
- Chat history lasts for the browser session only.

## Tech stack

Python, Streamlit, Google Gemini (`google-genai`), Pillow, Pollinations AI
