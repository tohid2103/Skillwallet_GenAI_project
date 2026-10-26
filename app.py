"""Multimodal Construction Intelligence Platform - Skill Wallet Capstone Project 1.
Single-file Streamlit app. No database. Deploy on Streamlit Community Cloud as-is.
"""
import io
import json
import re
import urllib.parse
from datetime import datetime

import streamlit as st
from PIL import Image

try:
    from google import genai
    from google.genai import types
    GENAI_OK = True
except ImportError:  # app still runs in demo mode
    GENAI_OK = False

st.set_page_config(page_title="Construction Intelligence Platform", page_icon="🏗️", layout="wide")

# ----------------------------------------------------------------- styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
h1, h2, h3 { font-family: 'Barlow Condensed', sans-serif; letter-spacing: .3px; }
.hero { background: #23272b; border-left: 10px solid #f2b705; padding: 22px 28px; border-radius: 4px; margin-bottom: 18px; }
.hero h1 { color: #fff; margin: 0; font-size: 2.3rem; }
.hero p { color: #b9c0c6; margin: 4px 0 0 0; }
.card { background: #fff; border: 1px solid #d9dde1; border-top: 4px solid #23272b; border-radius: 4px; padding: 14px 16px; }
.card .lbl { color: #5c656d; font-size: .82rem; }
.card .val { font-family: 'Barlow Condensed'; font-size: 2rem; font-weight: 700; color: #23272b; line-height: 1.1; }
.pill { display: inline-block; padding: 3px 12px; border-radius: 999px; font-weight: 600; font-size: .85rem; color: #fff; }
.ok { background: #2e7d32; } .warn { background: #b26a00; } .bad { background: #c62828; } .crit { background: #6a1b1b; } .low { background: #546e7a; }
.alert { border-left: 6px solid #f2b705; background: #fff8e1; padding: 10px 14px; margin: 8px 0; border-radius: 3px; color: #23272b; }
.alert.red { border-color: #c62828; background: #fdecea; }
@media (prefers-color-scheme: dark) {
  .card { background: #2a2f34; border-color: #3d444a; border-top-color: #f2b705; }
  .card .val { color: #fff; } .card .lbl { color: #aab2b9; }
  .alert { background: #3a3320; color: #f1f1f1; } .alert.red { background: #3b2220; }
}
</style>
""", unsafe_allow_html=True)

SEV_CLASS = {"low": "low", "medium": "warn", "high": "bad", "critical": "crit"}
MODEL_DEFAULT = "gemini-2.5-flash"

# ----------------------------------------------------------------- helpers
def pill(text: str, cls: str) -> str:
    return f'<span class="pill {cls}">{text}</span>'


def metric(label: str, value: str) -> str:
    return f'<div class="card"><div class="lbl">{label}</div><div class="val">{value}</div></div>'


def inr(amount: float) -> str:
    if amount >= 1e7:
        return f"₹{amount / 1e7:,.2f} Cr"
    return f"₹{amount / 1e5:,.2f} L"


def get_client():
    key = st.session_state.get("api_key", "").strip()
    if GENAI_OK and key:
        return genai.Client(api_key=key)
    return None


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def analyze_image(file, prompt: str, demo: dict) -> tuple[dict, bool]:
    """Returns (result, is_demo). Falls back to demo data on any failure."""
    client = get_client()
    if client is None:
        return demo, True
    try:
        img = Image.open(io.BytesIO(file.getvalue())).convert("RGB")
        resp = client.models.generate_content(
            model=st.session_state.get("model", MODEL_DEFAULT),
            contents=[prompt, img],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2),
        )
        return parse_json(resp.text), False
    except Exception as exc:
        st.warning(f"Live analysis failed ({type(exc).__name__}: {str(exc)[:160]}). Showing demonstration output.")
        return demo, True


def download(label: str, data: dict, name: str):
    st.download_button(label, json.dumps(data, indent=2), file_name=f"{name}_{datetime.now():%Y%m%d_%H%M}.json",
                       mime="application/json")

# ----------------------------------------------------------------- prompts & demo data
SAFETY_PROMPT = """You are a certified construction safety officer. Audit this site photo against OSHA 29 CFR 1926
and IS 456 / NBC 2016 site practice. Check each worker for: helmet, high-vis vest, steel-toe boots, safety harness
(where work at height). Return ONLY JSON with this schema:
{"safety_score": int 0-100, "overall_status": "Compliant|Needs Attention|Non-Compliant",
 "workers_detected": int,
 "ppe_detection": {"helmet": {"status": "Present|Missing|Not Visible", "note": str}, "high_vis_vest": {...}, "steel_toe_boots": {...}, "safety_harness": {...}},
 "hazards": [{"hazard": str, "severity": "Low|Medium|High|Critical", "standard": str, "remedy": str}],
 "summary": str}
Only report what is visible; use "Not Visible" rather than guessing."""

CRACK_PROMPT = """You are a structural engineer. Examine this concrete/masonry surface image. Return ONLY JSON:
{"defect_type": "Hairline|Settlement|Structural Shear|Thermal Expansion|Spalling",
 "confidence": float 0-1, "estimated_crack_width_mm": float, "pattern": str (e.g. diagonal, vertical, map-cracking),
 "root_causes": [str], "recommended_repairs": [{"method": str, "detail": str}],
 "urgency": "Low|Medium|High|Critical", "monitoring_advice": str, "disclaimer": str}
Reference IS 456 crack-width limits (0.3 mm general exposure). Be conservative; recommend a site inspection when uncertain."""

DEMO_SAFETY = {
    "safety_score": 62, "overall_status": "Needs Attention", "workers_detected": 3,
    "ppe_detection": {
        "helmet": {"status": "Present", "note": "2 of 3 workers wearing helmets"},
        "high_vis_vest": {"status": "Present", "note": "All workers visible in vests"},
        "steel_toe_boots": {"status": "Not Visible", "note": "Footwear not clearly visible"},
        "safety_harness": {"status": "Missing", "note": "Worker at elevated edge without harness"}},
    "hazards": [
        {"hazard": "Unprotected edge at elevated slab", "severity": "Critical", "standard": "OSHA 1926.501",
         "remedy": "Install guardrails/toe-boards and mandate full-body harness tied to anchor points."},
        {"hazard": "Loose material stacked near working area", "severity": "Medium", "standard": "OSHA 1926.250",
         "remedy": "Relocate and stack materials on stable ground away from edges."},
        {"hazard": "Worker without helmet", "severity": "High", "standard": "OSHA 1926.100",
         "remedy": "Stop work for the individual until IS 2925 helmet is worn; toolbox talk."}],
    "summary": "DEMO DATA: Partial PPE compliance with a critical fall-protection gap."}

DEMO_CRACK = {
    "defect_type": "Structural Shear", "confidence": 0.74, "estimated_crack_width_mm": 1.8,
    "pattern": "Diagonal (approx. 45°) stepping near opening",
    "root_causes": ["Differential settlement of footing", "Inadequate shear reinforcement near opening",
                    "Overloading / poor lintel bearing"],
    "recommended_repairs": [
        {"method": "Epoxy injection", "detail": "Low-viscosity epoxy pressure injection after cleaning and port installation."},
        {"method": "Structural re-grouting", "detail": "Non-shrink cementitious grout; add jacketing if movement continues."}],
    "urgency": "High",
    "monitoring_advice": "Fix tell-tale gauges across the crack and log width weekly for 8 weeks.",
    "disclaimer": "DEMO DATA. AI screening only; a licensed structural engineer must inspect before repair."}

# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("🏗️ Control Panel")
    st.text_input("Google Gemini API key", type="password", key="api_key",
                  help="Held in session memory only. Never stored or logged.")
    st.text_input("Model", value=MODEL_DEFAULT, key="model")
    live = bool(GENAI_OK and st.session_state.get("api_key", "").strip())
    st.markdown(pill("LIVE MODE" if live else "DEMO MODE", "ok" if live else "warn"), unsafe_allow_html=True)
    if not live:
        st.caption("No key supplied: sample outputs are shown so every feature can be explored.")
    st.divider()
    st.subheader("Architecture")
    st.markdown("""
- **UI**: Streamlit + custom CSS
- **Vision/LLM**: Gemini (multimodal, JSON mode)
- **Estimator**: rule-based Indian cost model
- **Renders**: Pollinations AI image URL
- **State**: `st.session_state` only, no database
""")
    st.divider()
    st.subheader("Modules")
    st.markdown("1. Safety & PPE Audit\n2. Crack Diagnostics\n3. Planning & Valuation\n4. Daily Site Assistant")
    st.caption("Skill Wallet Capstone Project 1")

st.markdown('<div class="hero"><h1>Multimodal Construction Intelligence Platform</h1>'
            '<p>Site safety, structural diagnostics, project valuation and daily advisory in one workspace.</p></div>',
            unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🦺 Safety & PPE Audit", "🧱 Crack Diagnostics", "📐 Planning & Valuation",
                                  "🌦️ Daily Site Assistant"])

# ----------------------------------------------------------------- tab 1
with tab1:
    st.subheader("Site Safety & PPE Audit")
    up = st.file_uploader("Upload a construction site photo", type=["jpg", "jpeg", "png"], key="safety_up")
    if up:
        c1, c2 = st.columns([1, 1.3])
        c1.image(up, use_container_width=True)
        if c2.button("Run safety audit", type="primary", key="run_safety"):
            with st.spinner("Auditing PPE and hazards..."):
                st.session_state["safety"] = analyze_image(up, SAFETY_PROMPT, DEMO_SAFETY)
    else:
        st.info("Upload a JPG or PNG to start the audit.")

    if "safety" in st.session_state and up:
        res, is_demo = st.session_state["safety"]
        if is_demo:
            st.caption("Showing demonstration output.")
        score = int(res.get("safety_score", 0))
        status = res.get("overall_status", "Unknown")
        cls = "ok" if score >= 80 else "warn" if score >= 55 else "bad"
        m = st.columns(4)
        m[0].markdown(metric("Safety score", f"{score}/100"), unsafe_allow_html=True)
        m[1].markdown(metric("Overall status", pill(status, cls)), unsafe_allow_html=True)
        m[2].markdown(metric("Workers detected", str(res.get("workers_detected", "-"))), unsafe_allow_html=True)
        m[3].markdown(metric("Hazards found", str(len(res.get("hazards", [])))), unsafe_allow_html=True)
        st.progress(max(0, min(score, 100)) / 100)
        st.write(res.get("summary", ""))

        st.markdown("#### PPE checklist")
        labels = {"helmet": "Helmet", "high_vis_vest": "High-vis vest", "steel_toe_boots": "Steel-toe boots",
                  "safety_harness": "Safety harness"}
        cols = st.columns(4)
        for col, (k, name) in zip(cols, labels.items()):
            item = res.get("ppe_detection", {}).get(k, {})
            s = item.get("status", "Not Visible")
            pc = {"Present": "ok", "Missing": "bad"}.get(s, "low")
            col.markdown(f"**{name}**<br>{pill(s, pc)}<br><small>{item.get('note', '')}</small>", unsafe_allow_html=True)

        st.markdown("#### Identified hazards")
        for h in res.get("hazards", []):
            sev = h.get("severity", "Low")
            with st.expander(f"{sev}: {h.get('hazard', '')}", expanded=sev.lower() in ("high", "critical")):
                st.markdown(pill(sev, SEV_CLASS.get(sev.lower(), "low")) + f" &nbsp; {h.get('standard', '')}",
                            unsafe_allow_html=True)
                st.write(f"**Remedy:** {h.get('remedy', '')}")
        download("Download JSON report", res, "safety_audit")

# ----------------------------------------------------------------- tab 2
with tab2:
    st.subheader("Crack Diagnostics & Structural Integrity")
    up2 = st.file_uploader("Upload a concrete or wall surface photo", type=["jpg", "jpeg", "png"], key="crack_up")
    if up2:
        c1, c2 = st.columns([1, 1.3])
        c1.image(up2, use_container_width=True)
        if c2.button("Diagnose defect", type="primary", key="run_crack"):
            with st.spinner("Classifying defect..."):
                st.session_state["crack"] = analyze_image(up2, CRACK_PROMPT, DEMO_CRACK)
    else:
        st.info("Upload a close-up of the cracked surface, ideally with a scale reference.")

    if "crack" in st.session_state and up2:
        res, is_demo = st.session_state["crack"]
        if is_demo:
            st.caption("Showing demonstration output.")
        urg = res.get("urgency", "Low")
        m = st.columns(4)
        m[0].markdown(metric("Defect type", res.get("defect_type", "-")), unsafe_allow_html=True)
        m[1].markdown(metric("Crack width", f"{res.get('estimated_crack_width_mm', '-')} mm"), unsafe_allow_html=True)
        m[2].markdown(metric("Confidence", f"{float(res.get('confidence', 0)) * 100:.0f}%"), unsafe_allow_html=True)
        m[3].markdown(metric("Urgency", pill(urg, SEV_CLASS.get(urg.lower(), "low"))), unsafe_allow_html=True)
        st.write(f"**Pattern:** {res.get('pattern', '-')}")
        a, b = st.columns(2)
        with a:
            st.markdown("#### Probable root causes")
            for c in res.get("root_causes", []):
                st.markdown(f"- {c}")
        with b:
            st.markdown("#### Recommended repairs")
            for r in res.get("recommended_repairs", []):
                st.markdown(f"- **{r.get('method', '')}**: {r.get('detail', '')}")
        st.markdown(f'<div class="alert">{res.get("monitoring_advice", "")}</div>', unsafe_allow_html=True)
        st.caption(res.get("disclaimer", ""))
        download("Download JSON report", res, "crack_diagnostics")

# ----------------------------------------------------------------- tab 3
STRUCT = {  # cost multiplier, steel kg/sqft, cement bags/sqft
    "RCC Framed Residential": (1.00, 4.0, 0.45),
    "Load-Bearing Masonry": (0.85, 2.2, 0.40),
    "Steel / PEB Industrial": (1.15, 6.5, 0.25),
    "Premium Villa (RCC)": (1.45, 4.5, 0.50),
    "Commercial Complex": (1.30, 5.0, 0.48),
}
TIER = {  # build cost INR/sqft, market value INR/sqft
    "Tier 1 (Mumbai, Delhi, Bengaluru)": (2600, 9500),
    "Tier 2 (Indore, Pune, Jaipur)": (2100, 5500),
    "Tier 3 (Smaller cities)": (1700, 3200),
}
MILESTONES = [(10, "Excavation"), (25, "Foundation"), (40, "Plinth"), (65, "Superstructure"),
              (85, "Finishing"), (100, "Handover")]

with tab3:
    st.subheader("Planning & Real Estate Valuation")
    c1, c2 = st.columns(2)
    stype = c1.selectbox("Structure type", list(STRUCT))
    tier = c2.selectbox("Location tier", list(TIER))
    area = c1.number_input("Built-up area (sqft)", min_value=100, max_value=500000, value=1800, step=50)
    done = c2.slider("Completion (%)", 0, 100, 40)

    mult, steel_psf, cem_psf = STRUCT[stype]
    cost_psf, mkt_psf = TIER[tier]
    budget = area * cost_psf * mult
    spent = budget * done / 100
    full_value = area * mkt_psf * (1.2 if "Premium" in stype else 1.0)
    value_now = full_value * (0.35 + 0.65 * done / 100)  # land/approvals share + built share

    m = st.columns(4)
    m[0].markdown(metric("Total project budget", inr(budget)), unsafe_allow_html=True)
    m[1].markdown(metric("Capex incurred", inr(spent)), unsafe_allow_html=True)
    m[2].markdown(metric("Current asset valuation", inr(value_now)), unsafe_allow_html=True)
    m[3].markdown(metric("Value at completion", inr(full_value)), unsafe_allow_html=True)

    steel_t = area * steel_psf / 1000
    cement = area * cem_psf
    m = st.columns(4)
    m[0].markdown(metric("Steel required", f"{steel_t:,.1f} tonnes"), unsafe_allow_html=True)
    m[1].markdown(metric("Cement required", f"{cement:,.0f} bags"), unsafe_allow_html=True)
    m[2].markdown(metric("Steel remaining", f"{steel_t * (1 - done / 100):,.1f} t"), unsafe_allow_html=True)
    m[3].markdown(metric("Cement remaining", f"{cement * (1 - done / 100):,.0f} bags"), unsafe_allow_html=True)

    st.markdown("#### Milestone progress")
    st.progress(done / 100)
    current = next((n for p, n in MILESTONES if done <= p), "Handover")
    cols = st.columns(len(MILESTONES))
    for col, (p, n) in zip(cols, MILESTONES):
        col.markdown(f"{'✅' if done >= p else '⬜'} **{n}**<br><small>{p}%</small>", unsafe_allow_html=True)
    st.caption(f"Current phase: {current}. Estimates use thumb-rule rates; confirm with a quantity surveyor and local registry rates.")

    st.markdown("#### Conceptual 3D architectural rendering")
    style = st.text_input("Style notes", "modern minimalist facade, large windows, landscaped entrance")
    if st.button("Generate rendering", key="render"):
        prompt = (f"3D architectural rendering of a {stype.lower()} building, {int(area)} sqft, Indian {tier.split(' (')[0]} "
                  f"city, {style}, photorealistic, golden hour, high detail")
        url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + "?width=1024&height=640&nologo=true"
        st.session_state["render_url"], st.session_state["render_prompt"] = url, prompt
    if "render_url" in st.session_state:
        try:
            st.image(st.session_state["render_url"], caption="Conceptual render (AI-generated, not a design drawing)",
                     use_container_width=True)
        except Exception:
            st.warning("Rendering service unavailable. Try again shortly.")
        st.code(st.session_state["render_prompt"], language="text")

# ----------------------------------------------------------------- tab 4
WEATHER = {
    "Normal": ("ok", ["Conduct routine toolbox talk and PPE checks.",
                      "Normal crane, scaffold and concrete operations permitted with standard inspections."]),
    "High Wind": ("red", ["Suspend crane and hoist operations when wind exceeds the manufacturer limit (typically ~36 km/h).",
                          "Secure loose sheeting, formwork, scaffolding boards and stacked materials.",
                          "Stop work at height; keep workers off open edges and unbraced scaffolds."]),
    "Heavy Rain": ("red", ["Electrical hazard: isolate temporary power, use RCCB/ELCB-protected outlets, keep cables off wet ground.",
                           "Cover fresh concrete and cement stocks; halt concreting if rainfall may wash out cement paste.",
                           "Check excavation and trench shoring for collapse risk; run dewatering pumps.",
                           "Anti-slip precautions on ramps, scaffolds and stairs."]),
    "Extreme Heat": ("", ["Enforce water-shade-rest cycles; schedule heavy work before 11 AM and after 4 PM.",
                          "Concrete curing protocol: start curing early, use wet hessian/curing compound, keep concrete cool, "
                          "and prefer evening pours; keep curing for at least 7 days (IS 456).",
                          "Watch for heat exhaustion symptoms; arrange ORS and first-aid."]),
}
CHAT_SYSTEM = ("You are a senior construction engineer assisting an Indian site team. Give practical, concise, "
               "standards-aware answers (IS codes, NBC 2016, OSHA). State assumptions, flag safety risks first, "
               "and advise consulting a licensed engineer for structural decisions.")


def demo_reply(q: str) -> str:
    q = q.lower()
    if "cure" in q or "curing" in q:
        return "Demo mode: Keep concrete continuously moist for at least 7 days (10 days for blended cements or hot weather) per IS 456."
    if "cement" in q or "mix" in q:
        return "Demo mode: M20 is commonly 1:1.5:3 by nominal mix; prefer design mix for M25 and above. Keep water-cement ratio at or below 0.5."
    if "steel" in q or "rebar" in q:
        return "Demo mode: Use Fe500/Fe500D TMT, maintain specified cover (e.g. 25 mm for slabs, 40 mm for columns) and lap lengths per IS 456."
    return "Demo mode: add a Gemini API key in the sidebar for full answers. Meanwhile, ask about curing, mix ratios or rebar."


with tab4:
    st.subheader("Daily Site Assistant & Weather-Aware Advisory")
    w = st.radio("Today's weather condition", list(WEATHER), horizontal=True)
    kind, alerts = WEATHER[w]
    for a in alerts:
        st.markdown(f'<div class="alert {"red" if kind == "red" else ""}">{a}</div>', unsafe_allow_html=True)

    st.markdown("#### Engineering assistant")
    if "chat" not in st.session_state:
        st.session_state.chat = []
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if q := st.chat_input("Ask about mix design, curing, scheduling, safety..."):
        st.session_state.chat.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            client = get_client()
            if client is None:
                reply = demo_reply(q)
            else:
                try:
                    history = [types.Content(role="user" if m["role"] == "user" else "model",
                                             parts=[types.Part(text=m["content"])]) for m in st.session_state.chat]
                    resp = client.models.generate_content(
                        model=st.session_state.get("model", MODEL_DEFAULT), contents=history,
                        config=types.GenerateContentConfig(
                            system_instruction=f"{CHAT_SYSTEM} Current site weather: {w}.", temperature=0.4))
                    reply = resp.text
                except Exception as exc:
                    reply = f"The assistant could not respond ({type(exc).__name__}). Check your API key and try again."
            st.markdown(reply)
        st.session_state.chat.append({"role": "assistant", "content": reply})
    if st.session_state.chat and st.button("Clear conversation"):
        st.session_state.chat = []
        st.rerun()
