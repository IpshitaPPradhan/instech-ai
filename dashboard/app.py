"""
Instech-AI Dashboard.
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from datetime import date, timedelta
import os

API = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="instech-ai", page_icon="◈", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'JetBrains Mono', monospace !important;
    background: #0a1628 !important;
    color: #e8e0cc !important;
}
section[data-testid="stSidebar"] {
    background: #060e1a !important;
    border-right: 0.5px solid #1e3358 !important;
}
section[data-testid="stSidebar"] * { font-family: 'JetBrains Mono', monospace !important; }
.stRadio label { color: #8899bb !important; font-size: 12px !important; }
h1,h2,h3 { color: #c9a84c !important; font-family: 'JetBrains Mono', monospace !important; font-weight:500 !important; }

.card {
    background: #0f1f3a;
    border: 0.5px solid #1e3358;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
}
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }
.stat-block { background: #0a1628; border: 0.5px solid #1e3358; border-radius: 8px; padding: 10px 14px; }
.stat-label { font-size: 10px; color: #8899bb; margin: 0 0 3px; letter-spacing:.03em; }
.stat-val   { font-size: 22px; font-weight: 700; margin: 0; color: #e8e0cc; }

.claim-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    font-size: 11px;
    color: #ccd6ee;
    border-top: 0.5px solid #1e3358;
}
.claim-row-header { border-top: none !important; color: #8899bb; padding-top: 0; }

.badge {
    display: inline-block;
    font-size: 10px;
    padding: 2px 10px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}
.b-pending   { background:#1a1f2b; color:#8899bb; border:0.5px solid #8899bb55; }
.b-approved  { background:#0d2218; color:#4ade80; border:0.5px solid #22c55e44; }
.b-denied    { background:#2b0a0a; color:#f87171; border:0.5px solid #ef444444; }
.b-flag      { background:#2b0a0a; color:#f87171; border:0.5px solid #ef444444; }
.b-review    { background:#2b1f00; color:#c9a84c; border:0.5px solid #c9a84c55; }
.b-clear     { background:#0d2218; color:#4ade80; border:0.5px solid #22c55e44; }
.b-trigger   { background:#1a0a2b; color:#a78bfa; border:0.5px solid #7c3aed55; }
.b-none      { background:#1a1f2b; color:#8899bb; border:0.5px solid #8899bb33; }

.verdict {
    font-size: 10px;
    margin-top: 12px;
    padding: 8px 12px;
    border-radius: 6px;
    background: #c9a84c14;
    border: 0.5px solid #c9a84c33;
    color: #c9a84c;
}
.verdict.triggered { background:#1a0a2b; border-color:#7c3aed55; color:#a78bfa; }

.tag {
    display: inline-block;
    font-size: 10px;
    padding: 3px 10px;
    border-radius: 4px;
    background: #c9a84c18;
    color: #c9a84c;
    border: 0.5px solid #c9a84c44;
    letter-spacing: .04em;
    margin-bottom: 10px;
}

.stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
    background: #0f1f3a !important;
    border: 0.5px solid #1e3358 !important;
    color: #e8e0cc !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stTextArea label, .stDateInput label {
    color: #8899bb !important;
    font-size: 11px !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stButton button {
    background: transparent !important;
    border: 0.5px solid #c9a84c !important;
    color: #c9a84c !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    padding: 4px 14px !important;
}
.stButton button:hover { opacity: .7; }
.streamlit-expanderHeader {
    background: #0f1f3a !important;
    border: 0.5px solid #1e3358 !important;
    border-radius: 6px !important;
    color: #8899bb !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}
.streamlit-expanderContent { background: #0a1422 !important; border: 0.5px solid #1e3358 !important; }
.stTabs [data-baseweb="tab"] { color: #8899bb !important; font-family: 'JetBrains Mono', monospace !important; font-size: 12px !important; }
.stTabs [aria-selected="true"] { color: #c9a84c !important; border-bottom-color: #c9a84c !important; }
hr { border-color: #1e3358 !important; }
p, li, span { font-family: 'JetBrains Mono', monospace !important; }
</style>
""", unsafe_allow_html=True)

# ── helpers ───────────────────────────────────────────────────────────────────
def api_get(path):
    try:
        r = requests.get(f"{API}{path}", timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API: {e}")
        return None

def api_post(path, payload={}):
    try:
        r = requests.post(f"{API}{path}", json=payload, timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API: {e}")
        return None

def badge(label, kind):
    return f'<span class="badge b-{kind}">{label}</span>'

def risk_colour(score):
    if score is None: return "#8899bb"
    if score > 0.7:   return "#f87171"
    if score > 0.4:   return "#c9a84c"
    return "#4ade80"

def fmt_inr(amount):
    if amount >= 10_000_000: return f"₹{amount/10_000_000:.1f}Cr"
    if amount >= 100_000:    return f"₹{amount/100_000:.1f}L"
    return f"₹{amount:,.0f}"

def claim_badge_kind(status):
    return {"pending":"pending","approved":"approved","denied":"denied","auto_triggered":"trigger"}.get(status,"none")

def fraud_badge_kind(decision):
    return {"flag":"flag","review":"review","clear":"clear"}.get(decision,"none")

# ── sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    '<p style="color:#c9a84c;font-size:16px;font-weight:700;margin-bottom:0">◈ instech-ai</p>'
    '<p style="color:#8899bb;font-size:10px;margin-top:2px;letter-spacing:.04em">ML-POWERED INSURANCE PLATFORM</p>',
    unsafe_allow_html=True
)
st.sidebar.markdown('<hr style="border-color:#1e3358;margin:10px 0">', unsafe_allow_html=True)
page = st.sidebar.radio("", ["dashboard","customers","policies","claims","parametric trigger"],
                         label_visibility="collapsed")

# ═════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
if page == "dashboard":
    st.markdown("## policy exposure map")

    customers = api_get("/customers/?limit=500") or []
    policies  = api_get("/policies/?limit=500")  or []
    claims    = api_get("/claims/?limit=500")     or []

    active    = [p for p in policies if p.get("status") == "active"]
    open_cl   = [c for c in claims   if c.get("status") == "pending"]
    flagged   = [c for c in claims   if (c.get("fraud_probability") or 0) > 0.7]
    high_risk = [p for p in policies if (p.get("risk_score") or 0) > 0.7]
    avg_risk  = (sum(p.get("risk_score") or 0 for p in policies) / len(policies)) if policies else 0

    ar_col = "#f87171" if avg_risk>0.7 else ("#c9a84c" if avg_risk>0.4 else "#4ade80")

    st.markdown(f"""
    <div class="card">
        <span class="tag">live metrics</span>
        <div class="stat-grid">
            <div class="stat-block"><p class="stat-label">customers</p>
                <p class="stat-val" style="color:#c9a84c">{len(customers)}</p></div>
            <div class="stat-block"><p class="stat-label">active policies</p>
                <p class="stat-val" style="color:#c9a84c">{len(active)}</p></div>
            <div class="stat-block"><p class="stat-label">avg risk score</p>
                <p class="stat-val" style="color:{ar_col}">{avg_risk:.2f}</p></div>
            <div class="stat-block"><p class="stat-label">fraud flagged</p>
                <p class="stat-val" style="color:#f87171">{len(flagged)}</p></div>
        </div>
    </div>""", unsafe_allow_html=True)

    # recent claims card
    recent = sorted(claims, key=lambda x: x.get("created_at",""), reverse=True)[:6]
    if recent:
        rows = '<div class="claim-row claim-row-header"><span>recent claims</span><span>id · status</span></div>'
        for c in recent:
            fp  = c.get("fraud_probability")
            dec = ("flag" if fp>0.7 else ("review" if fp>0.4 else "clear")) if fp is not None else None
            b   = badge(dec, fraud_badge_kind(dec)) if dec else badge(c.get("status","pending"), claim_badge_kind(c.get("status","pending")))
            rows += f'<div class="claim-row"><span>CLM-{c["id"]:04d} · {c.get("claim_type","—")} · {fmt_inr(c.get("amount_requested",0))}</span>{b}</div>'

        trig = [p for p in policies if p.get("trigger_status")=="triggered"]
        if trig:
            p = trig[0]
            v = f'<div class="verdict triggered">◉ parametric trigger: flood confirmed at {p["lat"]:.2f}N {p["lon"]:.2f}E · payout eligible</div>'
        else:
            v = f'<div class="verdict">◈ {len(open_cl)} open claims · {len(high_risk)} high-risk policies</div>'

        st.markdown(f'<div class="card">{rows}{v}</div>', unsafe_allow_html=True)

    # map
    center = [20.5937, 78.9629]
    if policies: center = [policies[0]["lat"], policies[0]["lon"]]
    m = folium.Map(location=center, zoom_start=5, tiles="CartoDB dark_matter")
    for p in policies:
        score  = p.get("risk_score") or 0
        colour = risk_colour(score)
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=6 + score * 9,
            popup=folium.Popup(
                f"<b>Policy #{p['id']}</b><br>Type: {p['policy_type']}<br>"
                f"Risk: {score:.2f}<br>SI: {fmt_inr(p.get('sum_insured',0))}",
                max_width=180),
            color=colour, fill=True, fill_color=colour, fill_opacity=0.65, weight=1,
        ).add_to(m)
    st_folium(m, width="100%", height=500)

# ═════════════════════════════════════════════════════════════════════════════
# CUSTOMERS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "customers":
    st.markdown("## customers")
    with st.expander("+ new customer"):
        c1,c2,c3 = st.columns(3)
        name  = c1.text_input("name")
        email = c2.text_input("email")
        phone = c3.text_input("phone")
        if st.button("create customer"):
            r = api_post("/customers/", {"name":name,"email":email,"phone":phone or None})
            if r: st.success(f"customer #{r['id']} created."); st.rerun()

    for c in (api_get("/customers/?limit=500") or []):
        pols = api_get(f"/policies/?customer_id={c['id']}&limit=50") or []
        st.markdown(f"""
        <div class="card">
            <span class="tag">customer #{c['id']}</span>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px">
                <div>
                    <p style="color:#c9a84c;font-weight:700;font-size:14px;margin:0">{c['name']}</p>
                    <p style="color:#8899bb;font-size:11px;margin:3px 0 0">{c['email']} &nbsp;·&nbsp; {c.get('phone','—')}</p>
                </div>
                <div style="text-align:right">
                    <p class="stat-label">policies</p>
                    <p style="color:#e8e0cc;font-size:20px;font-weight:700;margin:0">{len(pols)}</p>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# POLICIES
# ═════════════════════════════════════════════════════════════════════════════
elif page == "policies":
    st.markdown("## policies")
    customers = api_get("/customers/?limit=500") or []
    cust_map  = {c["id"]: c["name"] for c in customers}

    with st.expander("+ new policy  (risk scored automatically on creation)"):
        c1,c2 = st.columns(2)
        cid  = c1.selectbox("customer",[c["id"] for c in customers],format_func=lambda x:f"#{x} — {cust_map.get(x,'')}")
        addr = c2.text_input("address")
        c3,c4 = st.columns(2)
        lat  = c3.number_input("latitude", value=28.6315, format="%.4f")
        lon  = c4.number_input("longitude",value=77.2167, format="%.4f")
        c5,c6,c7,c8 = st.columns(4)
        ptype = c5.selectbox("type",["home","flood","fire","auto"])
        si    = c6.number_input("sum insured (₹)",value=5_000_000,step=500_000)
        prem  = c7.number_input("premium (₹/yr)", value=60_000,   step=5_000)
        sd    = c8.date_input("start",value=date.today())
        ed    = st.date_input("end",value=date.today()+timedelta(days=365))
        if st.button("create policy"):
            r = api_post("/policies/",{"customer_id":cid,"address":addr,"lat":lat,"lon":lon,
                                       "policy_type":ptype,"sum_insured":si,"premium":prem,
                                       "start_date":str(sd),"end_date":str(ed)})
            if r: st.success(f"policy #{r['id']} created · risk: {r.get('risk_score','—')}"); st.rerun()

    for p in (api_get("/policies/?limit=500") or []):
        score  = p.get("risk_score")
        sc_str = f"{score:.2f}" if score is not None else "—"
        sc_col = risk_colour(score)
        ts     = p.get("trigger_status","none")
        ts_b   = badge(ts, "trigger" if ts=="triggered" else "none")

        st.markdown(f"""
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div>
                    <span class="tag">{p['policy_type']}</span>
                    <p style="color:#c9a84c;font-weight:700;font-size:14px;margin:4px 0 2px">#{p['id']} — {p['address'][:45]}</p>
                    <p style="color:#8899bb;font-size:11px;margin:0">
                        SI: {fmt_inr(p.get('sum_insured',0))} &nbsp;·&nbsp; prem: {fmt_inr(p.get('premium',0))}/yr &nbsp;·&nbsp; {p.get('status','—')}
                    </p>
                </div>
                <div style="text-align:right">
                    <p class="stat-label">risk score</p>
                    <p style="color:{sc_col};font-size:22px;font-weight:700;margin:0 0 4px">{sc_str}</p>
                    {ts_b}
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        if st.button(f"↻ re-score #{p['id']}", key=f"rs_{p['id']}"):
            r = api_post(f"/policies/{p['id']}/risk-update")
            if r: st.info(f"risk: {r['risk_score']:.4f} | precip: {r['weather'].get('precip',0):.1f}mm"); st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# CLAIMS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "claims":
    st.markdown("## claims")
    policies = api_get("/policies/?limit=500") or []
    pol_map  = {p["id"]: p for p in policies}

    with st.expander("+ new claim"):
        c1,c2 = st.columns(2)
        pid   = c1.selectbox("policy",[p["id"] for p in policies],
                              format_func=lambda x:f"#{x} — {pol_map[x]['policy_type']} — {pol_map[x]['address'][:28]}")
        ctype = c2.selectbox("type",["flood","fire","theft","accident","other"])
        c3,c4 = st.columns(2)
        amt   = c3.number_input("amount (₹)",value=250_000,step=10_000)
        desc  = c4.text_input("description")
        if st.button("file claim"):
            r = api_post("/claims/",{"policy_id":pid,"claim_type":ctype,"amount_requested":amt,"description":desc or None})
            if r: st.success(f"claim #{r['id']} filed."); st.rerun()

    for c in (api_get("/claims/?limit=500") or []):
        fp     = c.get("fraud_probability")
        flags  = c.get("risk_flags") or []
        status = c.get("status","pending")
        dec    = ("flag" if fp>0.7 else ("review" if fp>0.4 else "clear")) if fp is not None else None
        fp_col = "#f87171" if (fp or 0)>0.7 else ("#c9a84c" if (fp or 0)>0.4 else "#4ade80")
        fp_str = f"{fp:.2f}" if fp is not None else "—"
        pol    = pol_map.get(c.get("policy_id"),{})
        flag_b = " ".join(badge(f,"review") for f in flags)
        dec_b  = badge(dec, fraud_badge_kind(dec)) if dec else badge("unchecked","none")
        st_b   = badge(status, claim_badge_kind(status))

        st.markdown(f"""
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div>
                    <span class="tag">{c.get('claim_type','—')}</span>
                    <p style="color:#c9a84c;font-weight:700;font-size:14px;margin:4px 0 2px">
                        CLM-{c['id']:04d} &nbsp;·&nbsp; {fmt_inr(c.get('amount_requested',0))}
                    </p>
                    <p style="color:#8899bb;font-size:11px;margin:0">
                        policy #{c.get('policy_id','—')} &nbsp;·&nbsp; {pol.get('address','')[:35]}
                    </p>
                </div>
                <div style="text-align:right;display:flex;flex-direction:column;gap:4px;align-items:flex-end">
                    {st_b}{dec_b}
                </div>
            </div>
            <div style="margin-top:10px;font-size:11px;color:#8899bb;display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                fraud prob: <span style="color:{fp_col};font-weight:700">{fp_str}</span>
                {flag_b}
            </div>
        </div>""", unsafe_allow_html=True)

        if st.button(f"⚑ fraud-check CLM-{c['id']:04d}", key=f"fc_{c['id']}"):
            r = api_post(f"/claims/{c['id']}/fraud-check")
            if r:
                d   = r["decision"]
                col = "#f87171" if d=="flag" else ("#c9a84c" if d=="review" else "#4ade80")
                st.markdown(
                    f'<div class="verdict" style="border-color:{col}44;color:{col}">'
                    f'decision: <b>{d}</b> &nbsp;·&nbsp; prob: {r["fraud_probability"]:.4f} &nbsp;·&nbsp; flags: {r["risk_flags"] or "none"}</div>',
                    unsafe_allow_html=True)
                st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# PARAMETRIC TRIGGER
# ═════════════════════════════════════════════════════════════════════════════
elif page == "parametric trigger":
    st.markdown("## parametric auto-trigger")
    st.markdown('<p style="color:#8899bb;font-size:12px;margin-top:-8px">CAT bond logic — fires on event threshold, not loss assessment.</p>',
                unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    lat        = c1.number_input("latitude",  value=28.6315, format="%.4f")
    lon        = c2.number_input("longitude", value=77.2167, format="%.4f")
    event_type = c3.selectbox("event type",["flood","fire","earthquake"])

    if st.button("evaluate trigger"):
        r = api_get(f"/claims/auto-trigger?lat={lat}&lon={lon}&event_type={event_type}")
        if r:
            triggered = r["triggered"]
            score     = r["flood_score"]
            precip    = r.get("total_precip_mm", 0)
            precip30  = r.get("precip_30d_mm", 0)
            elevation = r.get("elevation_m", 0)
            elev_risk = r.get("elevation_risk", 0)
            sc_col    = "#a78bfa" if triggered else "#8899bb"
            icon      = "◉ TRIGGERED" if triggered else "○ not triggered"
            v_cls     = "verdict triggered" if triggered else "verdict"

            st.markdown(f"""
            <div class="card">
                <span class="tag">{event_type}</span>
                <p style="font-size:18px;font-weight:700;color:{sc_col};margin:8px 0 4px">{icon}</p>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:12px;margin-bottom:0">
                    <div class="stat-block"><p class="stat-label">flood score</p>
                        <p class="stat-val" style="color:{sc_col}">{score:.4f}</p></div>
                    <div class="stat-block"><p class="stat-label">threshold</p>
                        <p class="stat-val">0.75</p></div>
                    <div class="stat-block"><p class="stat-label">elevation (real)</p>
                        <p class="stat-val">{elevation:.0f}m</p></div>
                    <div class="stat-block"><p class="stat-label">elevation risk</p>
                        <p class="stat-val">{elev_risk:.2f}</p></div>
                    <div class="stat-block"><p class="stat-label">7-day rain (real)</p>
                        <p class="stat-val">{precip:.1f}mm</p></div>
                    <div class="stat-block"><p class="stat-label">30-day baseline (real)</p>
                        <p class="stat-val">{precip30:.0f}mm</p></div>
                </div>
                <div class="{v_cls}" style="margin-top:12px">{r['message']}</div>
            </div>""", unsafe_allow_html=True)

            m = folium.Map(location=[lat, lon], zoom_start=8, tiles="CartoDB dark_matter")
            folium.CircleMarker(location=[lat,lon], radius=20,
                color="#a78bfa" if triggered else "#8899bb",
                fill=True, fill_opacity=0.35, weight=2).add_to(m)
            st_folium(m, width="100%", height=320)