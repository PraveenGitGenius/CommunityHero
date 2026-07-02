import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import random
import json
import re
import time
import base64
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import pandas as pd
from io import BytesIO

# ──────────────────────────────────────────
# CONFIG & SETUP
# ──────────────────────────────────────────
os.makedirs("uploads", exist_ok=True)

st.set_page_config(
    page_title="Community Hero",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────
# STYLES
# ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Page background ── */
.main { background: #F0F4F8; }

section[data-testid="stSidebar"] {
    background: #0A1628;
    border-right: 1px solid #1E3A5F;
}
section[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #FFFFFF !important; }

/* ── Hide default header ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 18px 22px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { font-size: .8rem !important; text-transform: uppercase; letter-spacing: .05em; color: #64748B !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    font-size: 14px;
    padding: 10px 22px;
    transition: all .2s;
    border: none;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0EA5E9, #2563EB);
    color: #fff;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(14,165,233,.35); }

/* ── Inputs ── */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div {
    border-radius: 10px !important;
    border: 1px solid #CBD5E1 !important;
    background: #FFFFFF !important;
}

/* ── Severity badges ── */
.badge-critical { background:#FEE2E2; color:#991B1B; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:600; }
.badge-high     { background:#FEF3C7; color:#92400E; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:600; }
.badge-medium   { background:#DBEAFE; color:#1E40AF; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:600; }
.badge-low      { background:#D1FAE5; color:#065F46; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:600; }

/* ── Report card ── */
.report-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
    transition: box-shadow .2s;
}
.report-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.09); }
.report-card-title { font-size: 15px; font-weight: 600; color: #0F172A; margin-bottom: 4px; }
.report-card-meta  { font-size: 13px; color: #64748B; margin-bottom: 8px; }
.report-id         { font-size: 11px; font-family: monospace; background:#F1F5F9; color:#475569; padding:2px 8px; border-radius:6px; }

/* ── Section header ── */
.sec-title {
    font-size: 20px;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 4px;
}
.sec-sub { font-size: 14px; color: #64748B; margin-bottom: 20px; }

/* ── AI panel ── */
.ai-panel {
    background: linear-gradient(135deg, #EFF6FF, #F0F9FF);
    border: 1px solid #BAE6FD;
    border-radius: 14px;
    padding: 20px;
    margin-top: 16px;
}
.ai-panel-header { font-size: 15px; font-weight: 700; color: #0369A1; margin-bottom: 14px; display:flex; align-items:center; gap:8px; }

/* ── Stat row ── */
.stat-row { display: flex; gap: 12px; flex-wrap: wrap; }
.stat-box { flex: 1; min-width: 80px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 16px; text-align: center; }
.stat-val  { font-size: 22px; font-weight: 700; color: #0F172A; }
.stat-lbl  { font-size: 11px; color: #64748B; text-transform: uppercase; letter-spacing: .04em; }

/* ── Leaderboard ── */
.lb-row { display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom:1px solid #F1F5F9; }
.lb-rank { width:28px; font-weight:700; font-size:14px; color:#64748B; text-align:center; }
.lb-avatar { width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:14px; flex-shrink:0; }
.lb-name { flex:1; font-weight:500; font-size:14px; color:#0F172A; }
.lb-pts  { font-weight:700; font-size:14px; color:#0EA5E9; }

/* ── XP bar ── */
.xp-bar { height:8px; background:#E2E8F0; border-radius:99px; overflow:hidden; margin:8px 0; }
.xp-fill { height:100%; background:linear-gradient(90deg,#0EA5E9,#6366F1); border-radius:99px; }

/* ── Timeline ── */
.timeline-item { display:flex; gap:12px; margin-bottom:16px; }
.tl-dot { width:10px; height:10px; border-radius:50%; background:#0EA5E9; flex-shrink:0; margin-top:5px; }
.tl-line { width:2px; background:#E2E8F0; flex-shrink:0; margin-left:4px; }
.tl-body { flex:1; }
.tl-title { font-size:13px; font-weight:600; color:#0F172A; }
.tl-meta  { font-size:12px; color:#64748B; margin-top:2px; }

/* ── Upload zone ── */
.upload-hint { background:#F8FAFC; border:2px dashed #CBD5E1; border-radius:12px; padding:32px; text-align:center; color:#94A3B8; margin-bottom:16px; }

/* ── Complaint box ── */
.complaint-box { background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:16px; font-size:13px; color:#334155; line-height:1.7; }

/* ── Info card ── */
.info-card { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:20px; }
.info-card-title { font-size:14px; font-weight:600; color:#0F172A; margin-bottom:12px; }

/* ── Achievement pill ── */
.ach { display:flex; align-items:center; gap:10px; padding:10px 14px; background:#F8FAFC; border-radius:10px; margin-bottom:8px; }
.ach-icon { font-size:20px; }
.ach-text { flex:1; font-size:13px; font-weight:500; color:#0F172A; }
.ach-pts  { font-size:12px; font-weight:700; color:#0EA5E9; }

/* ── Divider ── */
hr { border:none; border-top:1px solid #F1F5F9; margin:20px 0; }

/* ── Status indicator ── */
.status-dot-pending   { color:#F59E0B; }
.status-dot-verified  { color:#22C55E; }
.status-dot-rejected  { color:#EF4444; }
.status-dot-progress  { color:#3B82F6; }
.status-dot-resolved  { color:#8B5CF6; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────
CATEGORIES = ["Pothole", "Garbage / Waste", "Water Leakage", "Street Light", "Flooding", "Encroachment", "Vandalism", "Air Pollution", "Other"]
CAT_ICONS  = {"Pothole":"","Garbage / Waste":"","Water Leakage":"","Street Light":"","Flooding":"","Encroachment":"","Vandalism":"","Air Pollution":"","Other":""}
SEV_COLORS = {"Critical":"#EF4444","High":"#F59E0B","Medium":"#3B82F6","Low":"#22C55E"}
LEVEL_NAMES = ["Newcomer","Observer","Reporter","Activist","Champion","City Hero"]
LEVEL_XP    = [0, 100, 300, 600, 1000, 2000]

def load_reports():
    try:
        with open("reports.json","r") as f:
            return json.load(f)
    except:
        return []

def save_reports(reports):
    with open("reports.json","w") as f:
        json.dump(reports, f, indent=2)

def gen_id():
    return f"CH-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"

def sev_badge(priority):
    cls = priority.lower() if priority else "medium"
    return f'<span class="badge-{cls}">{priority}</span>'

def status_icon(status):
    icons = {"Pending":"🟡","Verified":"🟢","Rejected":"🔴","In Progress":"🔵","Resolved":"🟣"}
    return icons.get(status,"⚪")

def time_ago(ts_str):
    try:
        ts = datetime.fromisoformat(ts_str)
        delta = datetime.now() - ts
        if delta.seconds < 60: return "just now"
        if delta.seconds < 3600: return f"{delta.seconds//60}m ago"
        if delta.days == 0: return f"{delta.seconds//3600}h ago"
        return f"{delta.days}d ago"
    except:
        return "recently"

def get_level(xp):
    for i in range(len(LEVEL_XP)-1, -1, -1):
        if xp >= LEVEL_XP[i]:
            return i+1, LEVEL_NAMES[min(i, len(LEVEL_NAMES)-1)]
    return 1, LEVEL_NAMES[0]

def extract_json(text):
    """Robustly extract JSON from model output."""
    text = text.strip()
    # try to find JSON block
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try:
            return json.loads(m.group())
        except:
            pass
    # fallback: strip markdown fences
    text = re.sub(r'```json|```', '', text).strip()
    try:
        return json.loads(text)
    except:
        return {}

# ──────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────
def init_state():
    defaults = {
        "page": "Dashboard",
        "reports": load_reports(),
        "xp": 0,
        "achievements": [],
        "ai_result": None,
        "pending_report": None,
        "api_key_set": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ──────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 20px">
        <div style="font-size:22px;font-weight:800;color:#FFFFFF;letter-spacing:-.3px;">
             Community Hero
        </div>
        <div style="font-size:12px;color:#64748B;margin-top:2px;">
            AI-Powered Civic Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    # API key input
    with st.expander(" Configuration", expanded=not st.session_state.api_key_set):
        api_key = st.text_input("Gemini API Key", type="password", placeholder="", help="Get your key from Google AI Studio")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                st.session_state.api_key_set = True
                st.success("✓ Connected")
            except Exception as e:
                st.error("Invalid key")

    st.markdown("---")
    pages = ["Dashboard", "Report Issue", "Live Feed", "My Profile", "About"]
    for pg in (pages):
        active = "background:#1E3A5F;border-radius:8px;" if st.session_state.page == pg else ""
        if st.sidebar.button(pg, use_container_width=True, key=f"nav_{pg}"):
            st.session_state.page = pg
            st.rerun()

    st.markdown("---")
    reports = st.session_state.reports
    total  = len(reports)
    crit   = sum(1 for r in reports if r.get("priority")=="Critical")
    res    = sum(1 for r in reports if r.get("status") in ["Verified","Resolved"])
    st.markdown(f"""
    <div style="font-size:17px;color:#64748B;line-height:2">
      Total reports: <b style="color:#fff">{total}</b><br>
      Critical: <b style="color:#EF4444">{crit}</b><br>
      Resolved: <b style="color:#22C55E">{res}</b>
    </div>
    """, unsafe_allow_html=True)

    # XP display
    level, level_name = get_level(st.session_state.xp)
    next_xp = LEVEL_XP[min(level, len(LEVEL_XP)-1)]
    pct = min(int((st.session_state.xp / next_xp)*100), 100) if next_xp else 100
    st.markdown(f"""
    <div style="margin-top:16px;padding:14px;background:#1E3A5F;border-radius:12px">
        <div style="font-size:12px;color:#94A3B8;margin-bottom:4px">YOUR LEVEL</div>
        <div style="font-size:15px;font-weight:700;color:#FFFFFF">{level_name}</div>
        <div class="xp-bar"><div class="xp-fill" style="width:{pct}%"></div></div>
        <div style="font-size:11px;color:#64748B">{st.session_state.xp} / {next_xp} XP</div>
    </div>
    """, unsafe_allow_html=True)

    


# ──────────────────────────────────────────
# PAGE: DASHBOARD
# ──────────────────────────────────────────
if st.session_state.page == "Dashboard":
    st.markdown('<div class="sec-title">Community Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub"></div>', unsafe_allow_html=True)

    reports = st.session_state.reports

    # ── Metrics row ──
    col1, col2, col3, col4, col5 = st.columns(5)
    total    = len(reports)
    verified = sum(1 for r in reports if r.get("status")=="Verified")
    resolved = sum(1 for r in reports if r.get("status")=="Resolved")
    critical = sum(1 for r in reports if r.get("priority")=="Critical")
    pending  = sum(1 for r in reports if r.get("status")=="Pending")

    col1.metric("Total Reports",   total,    "All time")
    col2.metric("Verified",        verified, "Community validated")
    col3.metric("Resolved",        resolved, "Fixed by authorities")
    col4.metric("🔴 Critical",     critical, "Needs urgent action")
    col5.metric("Pending",         pending,  "Awaiting review")

    st.markdown("---")

    if not reports:
        st.info(" No reports yet. Head to **Report Issue** to submit the first one!")
        st.stop()

    # ── Charts row ──
    df = pd.DataFrame(reports)
    col_a, col_b, col_c = st.columns([1.2, 1, 1])

    with col_a:
        cat_counts = df["category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig_cat = px.pie(
            cat_counts, values="Count", names="Category",
            title="Issues by Category",
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.45
        )
        fig_cat.update_layout(
            margin=dict(t=40,b=0,l=0,r=0), height=280,
            legend=dict(font=dict(size=11)),
            title_font_size=14, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_b:
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status","Count"]
        color_map = {"Pending":"#F59E0B","Verified":"#22C55E","Rejected":"#EF4444","In Progress":"#3B82F6","Resolved":"#8B5CF6"}
        fig_st = px.bar(
            status_counts, x="Status", y="Count",
            title="Resolution Status",
            color="Status", color_discrete_map=color_map
        )
        fig_st.update_layout(
            showlegend=False, margin=dict(t=40,b=0,l=0,r=0), height=280,
            title_font_size=14, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#F1F5F9"), xaxis=dict(tickfont=dict(size=11))
        )
        fig_st.update_traces(marker_line_width=0)
        st.plotly_chart(fig_st, use_container_width=True)

    with col_c:
        if "severity" in df.columns:
            fig_sev = px.histogram(
                df, x="severity", nbins=10,
                title="Severity Distribution",
                color_discrete_sequence=["#0EA5E9"]
            )
            fig_sev.update_layout(
                margin=dict(t=40,b=0,l=0,r=0), height=280,
                title_font_size=14, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Severity Score", yaxis_title="Reports",
                yaxis=dict(gridcolor="#F1F5F9")
            )
            fig_sev.update_traces(marker_line_width=0)
            st.plotly_chart(fig_sev, use_container_width=True)

    # ── Map ──
    if "lat" in df.columns and "lon" in df.columns:
        map_df = df[["lat","lon","category","location","severity"]].dropna()
        if not map_df.empty:
            st.markdown("####  Map")
            fig_map = px.scatter_mapbox(
                map_df, lat="lat", lon="lon",
                hover_name="location",
                hover_data={"category":True,"severity":True,"lat":False,"lon":False},
                color="severity",
                color_continuous_scale="RdYlGn_r",
                size=[14]*len(map_df),
                zoom=11, height=380,
                mapbox_style="carto-positron"
            )
            fig_map.update_layout(margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("---")

    # ── AI Predictive Insights ──
    st.markdown("####  AI Predictive Insights")
    if len(reports) >= 2:
        top_cat = df["category"].value_counts().idxmax()
        avg_sev = round(df["severity"].mean(), 1) if "severity" in df.columns else 50
        resolution_rate = round((verified+resolved)/total*100) if total else 0

        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            st.info(f" **Hotspot alert:** {top_cat} accounts for the most reports. Schedule a dedicated inspection drive.")
        with col_i2:
            level_txt = "Critical — escalate immediately" if avg_sev > 65 else "Moderate — routine monitoring"
            st.warning(f" **Avg severity: {avg_sev}/100** — {level_txt}")
        with col_i3:
            color = "success" if resolution_rate > 50 else "warning"
            getattr(st, color)(f" **{resolution_rate}% resolution rate** — {'Good momentum!' if resolution_rate>50 else 'Needs improvement'}")
    else:
        st.info("Submit more reports to unlock AI predictive insights and trend analysis.")

    st.markdown("---")

    # ── Critical Issues ──
    critical_reports = [r for r in reports if r.get("priority") in ["Critical","High"]]
    if critical_reports:
        st.markdown("####  Critical Issues Requiring Immediate Action")
        for r in sorted(critical_reports, key=lambda x: x.get("severity",0), reverse=True)[:4]:
            sev = r.get("severity", 0)
            col_x, col_y = st.columns([5,1])
            with col_x:
                st.markdown(f"""
                <div class="report-card" style="border-left:4px solid {SEV_COLORS.get(r.get('priority','Medium'),'#gray')}">
                    <div class="report-card-title">{CAT_ICONS.get(r.get('category','Other'),'⚠️')} {r.get('category','Unknown')} — {r.get('location','Unknown')}</div>
                    <div class="report-card-meta">
                        {sev_badge(r.get('priority','Medium'))} &nbsp;
                        <span class="report-id">{r.get('report_id','N/A')}</span> &nbsp;
                        Severity: <b>{sev}/100</b> &nbsp;·&nbsp; {status_icon(r.get('status','Pending'))} {r.get('status','Pending')}
                    </div>
                    <div style="font-size:13px;color:#334155">{r.get('risk','')[:180]}...</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Export ──
    st.markdown("---")
    st.markdown("####  Export Data")
    csv_data = pd.DataFrame(reports).drop(columns=["analysis","complaint"],errors="ignore").to_csv(index=False)
    st.download_button("Download CSV Report", data=csv_data, file_name=f"community_hero_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")


# ──────────────────────────────────────────
# PAGE: REPORT ISSUE
# ──────────────────────────────────────────
elif st.session_state.page == "Report Issue":
    st.markdown('<div class="sec-title"> Report a Community Issue</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Upload a photo — our Gemini AI will instantly analyze, categorize, and draft an official complaint</div>', unsafe_allow_html=True)

    if not st.session_state.api_key_set:
        st.warning("⚠️ Please add your Gemini API key in the sidebar to enable AI analysis.")
        st.stop()

    col_form, col_result = st.columns([1, 1.1], gap="large")

    with col_form:
        # ── Upload ──
        st.markdown("##### Step 1 — Upload photo")
        uploaded = st.file_uploader("", type=["jpg","jpeg","png","webp"], label_visibility="collapsed")

        if uploaded:
            img = Image.open(uploaded)
            st.image(img, caption="Uploaded image", use_container_width=True)

        st.markdown("##### Step 2 — Location details")
        location  = st.text_input("Area / Locality", placeholder="e.g. Park Street, Kolkata")
        col_lat, col_lon = st.columns(2)
        latitude  = col_lat.number_input("Latitude",  value=22.5726, format="%.4f", step=0.0001)
        longitude = col_lon.number_input("Longitude", value=88.3639, format="%.4f", step=0.0001)
        extra_desc = st.text_area("Additional context (optional)", placeholder="Anything the AI might miss...", height=80)

        st.markdown("##### Step 3 — Analyze & Submit")
        analyze_btn = st.button(" Analyze with Gemini AI", type="primary", use_container_width=True, disabled=not (uploaded and location))

    # ── AI Analysis ──
    if analyze_btn and uploaded and location:
        with col_result:
            with st.spinner(" Gemini AI is analyzing your image..."):
                progress = st.progress(0)
                status_text = st.empty()

                try:
                    img_pil = Image.open(uploaded)
                    model = genai.GenerativeModel("gemini-2.5-flash")

                    prompt = f"""You are a senior civic issue analyst AI for the Community Hero platform in India.

Analyze this image of a community problem and respond with ONLY a valid JSON object (no markdown, no extra text):

{{
  "category": "<one of: Pothole, Garbage / Waste, Water Leakage, Street Light, Flooding, Encroachment, Vandalism, Air Pollution, Other>",
  "severity": <integer 0-100>,
  "priority": "<Critical|High|Medium|Low>",
  "risk": "<2-sentence risk description>",
  "action": "<2-sentence recommended immediate action>",
  "authority": "<specific responsible civic authority>",
  "impact_30_days": "<one sentence: consequence if ignored for 30 days>",
  "estimated_people_affected": <integer estimate>,
  "complaint": "<formal 3-paragraph complaint letter to the municipal authority, professional tone, include specific observations from the image, request urgent action, mention location: {location}>"
}}

Location context: {location}
Additional context: {extra_desc or 'None'}"""

                    status_text.text("Uploading image to Gemini...")
                    progress.progress(20)
                    time.sleep(0.3)

                    status_text.text("Running issue detection...")
                    progress.progress(50)

                    response = model.generate_content([prompt, img_pil])
                    progress.progress(80)

                    status_text.text("Parsing analysis results...")
                    ai = extract_json(response.text)

                    # Generate complaint separately if needed
                    if not ai.get("complaint"):
                        comp_prompt = f"""Write a formal 3-paragraph complaint letter to the Municipal Corporation regarding a {ai.get('category','civic')} issue at {location}. Be specific, professional, and request urgent action."""
                        comp_resp = model.generate_content([comp_prompt, img_pil])
                        ai["complaint"] = comp_resp.text

                    progress.progress(100)
                    status_text.empty()
                    progress.empty()

                    # Store result
                    report_id = gen_id()
                    img_path = f"uploads/{report_id}.jpg"
                    img_pil.save(img_path, "JPEG")

                    st.session_state.ai_result = ai
                    st.session_state.pending_report = {
                        "report_id": report_id,
                        "location": location,
                        "category": ai.get("category","Other"),
                        "severity": ai.get("severity", 50),
                        "priority": ai.get("priority","Medium"),
                        "risk": ai.get("risk",""),
                        "action": ai.get("action",""),
                        "authority": ai.get("authority","Municipal Corporation"),
                        "impact_30_days": ai.get("impact_30_days",""),
                        "estimated_people_affected": ai.get("estimated_people_affected", 0),
                        "analysis": response.text,
                        "complaint": ai.get("complaint",""),
                        "status": "Pending",
                        "upvotes": 0,
                        "downvotes": 0,
                        "image": img_path,
                        "lat": latitude,
                        "lon": longitude,
                        "timestamp": datetime.now().isoformat(),
                    }

                    st.success("✅ Analysis complete!")

                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    st.info("Make sure your Gemini API key is valid and has image analysis permissions.")

    # ── Show result ──
    with col_result:
        ai   = st.session_state.get("ai_result")
        pend = st.session_state.get("pending_report")

        if ai and pend:
            st.markdown(f"""
            <div class="ai-panel">
                <div class="ai-panel-header"> Gemini AI Analysis Complete</div>
                <div class="stat-row">
                    <div class="stat-box">
                        <div class="stat-val">{ai.get('severity',50)}</div>
                        <div class="stat-lbl">Severity /100</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-val" style="font-size:15px">{ai.get('priority','—')}</div>
                        <div class="stat-lbl">Priority</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-val" style="font-size:13px">{ai.get('estimated_people_affected',0):,}</div>
                        <div class="stat-lbl">People Affected</div>
                    </div>
                </div>
                <hr style="margin:14px 0">
                <div style="margin-bottom:10px">
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#0369A1;margin-bottom:4px">Category Detected</div>
                    <div style="font-size:14px;font-weight:600;color:#0F172A">{CAT_ICONS.get(ai.get('category','Other'),'⚠️')} {ai.get('category','Other')}</div>
                </div>
                <div style="margin-bottom:10px">
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#0369A1;margin-bottom:4px">Risk Description</div>
                    <div style="font-size:13px;color:#334155;line-height:1.6">{ai.get('risk','—')}</div>
                </div>
                <div style="margin-bottom:10px">
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#0369A1;margin-bottom:4px">Recommended Action</div>
                    <div style="font-size:13px;color:#334155;line-height:1.6">{ai.get('action','—')}</div>
                </div>
                <div style="margin-bottom:10px">
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#0369A1;margin-bottom:4px">Impact if Ignored (30 Days)</div>
                    <div style="font-size:13px;color:#334155;line-height:1.6">{ai.get('impact_30_days','—')}</div>
                </div>
                <div>
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#0369A1;margin-bottom:4px">Responsible Authority</div>
                    <div style="font-size:13px;color:#334155;font-weight:600">{ai.get('authority','Municipal Corporation')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Complaint letter
            st.markdown("---")
            st.markdown("#####  Official Complaint Letter (AI-Generated)")
            complaint_text = ai.get("complaint","")
            st.text_area("", value=complaint_text, height=240, label_visibility="collapsed")

            col_dl, col_sub = st.columns(2)
            with col_dl:
                st.download_button(
                    "📥 Download Complaint",
                    data=complaint_text,
                    file_name=f"{pend['report_id']}_complaint.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with col_sub:
                if st.button("📤 Submit Report", type="primary", use_container_width=True):
                    st.session_state.reports.append(pend)
                    save_reports(st.session_state.reports)
                    st.session_state.xp += 50
                    if len(st.session_state.reports) == 1:
                        st.session_state.achievements.append("first_report")
                    st.session_state.ai_result = None
                    st.session_state.pending_report = None
                    st.success(f"✅ Report {pend['report_id']} submitted! You earned +50 XP.")
                    time.sleep(1.5)
                    st.session_state.page = "Live Feed"
                    st.rerun()
        else:
            st.markdown("""
            <div class="upload-hint">
                <div style="font-size:40px;margin-bottom:12px">🤖</div>
                <div style="font-size:15px;font-weight:600;color:#475569">AI analysis results appear here</div>
                <div style="font-size:13px;margin-top:6px">Upload a photo and enter your location to get started</div>
            </div>
            """, unsafe_allow_html=True)


# ──────────────────────────────────────────
# PAGE: LIVE FEED
# ──────────────────────────────────────────
elif st.session_state.page == "Live Feed":
    st.markdown('<div class="sec-title"> Live Issue Feed</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Community-reported issues — verify, upvote, and track resolution</div>', unsafe_allow_html=True)

    reports = st.session_state.reports

    if not reports:
        st.info(" No reports yet. Be the first to report a community issue!")
        if st.button("+ Report an Issue", type="primary"):
            st.session_state.page = "Report Issue"
            st.rerun()
        st.stop()

    # ── Filters ──
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    filter_cat    = col_f1.selectbox("Category", ["All"] + CATEGORIES)
    filter_status = col_f2.selectbox("Status", ["All","Pending","Verified","Rejected","In Progress","Resolved"])
    filter_pri    = col_f3.selectbox("Priority", ["All","Critical","High","Medium","Low"])
    sort_by       = col_f4.selectbox("Sort by", ["Newest","Highest Severity","Most Votes"])
    search_q      = st.text_input("🔍 Search by location or report ID", placeholder="e.g. Park Street or CH-20260622")

    # Apply filters
    filtered = reports[:]
    if filter_cat    != "All": filtered = [r for r in filtered if r.get("category")==filter_cat]
    if filter_status != "All": filtered = [r for r in filtered if r.get("status")==filter_status]
    if filter_pri    != "All": filtered = [r for r in filtered if r.get("priority")==filter_pri]
    if search_q:
        q = search_q.lower()
        filtered = [r for r in filtered if q in r.get("location","").lower() or q in r.get("report_id","").lower()]

    if sort_by == "Newest":         filtered = sorted(filtered, key=lambda r: r.get("timestamp",""), reverse=True)
    elif sort_by == "Highest Severity": filtered = sorted(filtered, key=lambda r: r.get("severity",0), reverse=True)
    elif sort_by == "Most Votes":    filtered = sorted(filtered, key=lambda r: r.get("upvotes",0), reverse=True)

    st.markdown(f"Showing **{len(filtered)}** of {len(reports)} reports")
    st.markdown("---")

    for i, r in enumerate(filtered):
        sev   = r.get("severity",0)
        pri   = r.get("priority","Medium")
        color = SEV_COLORS.get(pri,"#64748B")

        col_card, col_actions = st.columns([4, 1])

        with col_card:
            img_path = r.get("image","")
            has_img  = os.path.exists(img_path) if img_path else False

            c1, c2 = st.columns([1, 3]) if has_img else st.columns([0,1])
            if has_img:
                with c1:
                    st.image(img_path, use_container_width=True)
            with c2:
                st.markdown(f"""
                <div class="report-card" style="border-left:4px solid {color}">
                    <div class="report-card-title">
                        {CAT_ICONS.get(r.get('category','Other'),'⚠️')} {r.get('category','Unknown')} — {r.get('location','Unknown location')}
                    </div>
                    <div class="report-card-meta">
                        {sev_badge(pri)} &nbsp;
                        <span class="report-id">{r.get('report_id','N/A')}</span> &nbsp;
                        Severity: <b>{sev}/100</b> &nbsp;·&nbsp;
                        {status_icon(r.get('status','Pending'))} <b>{r.get('status','Pending')}</b>
                        &nbsp;·&nbsp; {time_ago(r.get('timestamp',''))}
                    </div>
                    <div style="font-size:13px;color:#475569;margin-top:6px;line-height:1.6">
                        📍 {r.get('location','')} &nbsp;·&nbsp; 🏛️ {r.get('authority','')}
                    </div>
                    <div style="font-size:13px;color:#334155;margin-top:8px">{r.get('risk','')[:200]}...</div>
                    <div style="margin-top:10px;font-size:13px;color:#64748B">
                        👍 {r.get('upvotes',0)} verified &nbsp; 👎 {r.get('downvotes',0)} disputed
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col_actions:
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            rid = r.get("report_id","")

            if st.button("👍 Verify", key=f"up_{rid}_{i}", use_container_width=True):
                for rep in st.session_state.reports:
                    if rep.get("report_id")==rid:
                        rep["upvotes"] = rep.get("upvotes",0)+1
                        rep["status"]  = "Verified"
                        break
                save_reports(st.session_state.reports)
                st.session_state.xp += 10
                st.rerun()

            if st.button("👎 Dispute", key=f"dn_{rid}_{i}", use_container_width=True):
                for rep in st.session_state.reports:
                    if rep.get("report_id")==rid:
                        rep["downvotes"] = rep.get("downvotes",0)+1
                        if rep["downvotes"] > rep.get("upvotes",0):
                            rep["status"] = "Rejected"
                        break
                save_reports(st.session_state.reports)
                st.rerun()

            if st.button("✅ Mark Resolved", key=f"res_{rid}_{i}", use_container_width=True):
                for rep in st.session_state.reports:
                    if rep.get("report_id")==rid:
                        rep["status"] = "Resolved"
                        break
                save_reports(st.session_state.reports)
                st.session_state.xp += 100
                st.rerun()


# ──────────────────────────────────────────
# PAGE: MY PROFILE (Gamification)
# ──────────────────────────────────────────
elif st.session_state.page == "My Profile":
    st.markdown('<div class="sec-title">👤 My Civic Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Track your impact, earn XP, and climb the community leaderboard</div>', unsafe_allow_html=True)

    xp = st.session_state.xp
    level, level_name = get_level(xp)
    next_xp = LEVEL_XP[min(level, len(LEVEL_XP)-1)]
    pct = min(int((xp / next_xp)*100), 100) if next_xp else 100

    col_p, col_lb = st.columns([1, 1.2])

    with col_p:
        st.markdown(f"""
        <div class="info-card">
            <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px">
                <div style="width:60px;height:60px;border-radius:50%;background:#EFF6FF;border:2px solid #BAE6FD;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:700;color:#0369A1">Y</div>
                <div>
                    <div style="font-size:18px;font-weight:700;color:#0F172A">You</div>
                    <div style="font-size:13px;color:#64748B">Level {level} — {level_name}</div>
                </div>
            </div>
            <div style="margin-bottom:16px">
                <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#64748B;margin-bottom:6px">XP Progress</div>
                <div style="font-size:22px;font-weight:700;color:#0EA5E9;margin-bottom:6px">{xp} XP</div>
                <div class="xp-bar"><div class="xp-fill" style="width:{pct}%"></div></div>
                <div style="font-size:12px;color:#94A3B8;margin-top:4px">{xp} / {next_xp} XP to Level {min(level+1, len(LEVEL_NAMES))}</div>
            </div>
            <hr>
            <div>
                <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#64748B;margin-bottom:10px">Your Stats</div>
                <div style="display:flex;gap:12px">
                    <div class="stat-box"><div class="stat-val">{len(st.session_state.reports)}</div><div class="stat-lbl">Reports</div></div>
                    <div class="stat-box"><div class="stat-val">{xp}</div><div class="stat-lbl">XP Earned</div></div>
                    <div class="stat-box"><div class="stat-val">{level}</div><div class="stat-lbl">Level</div></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown("##### 🏆 Achievements")

        achievements = [
            ("🎯","First Report","Submit your first issue",50, len(st.session_state.reports)>=1),
            ("🔥","On a Roll","Submit 3 reports",100, len(st.session_state.reports)>=3),
            ("👥","Community Verifier","Verify 5 reports",150, xp>=60),
            ("⚡","Issue Resolver","Get a report resolved",200, any(r.get("status")=="Resolved" for r in st.session_state.reports)),
            ("🏆","City Champion","Reach Level 3",300, level>=3),
            ("🌟","City Hero","Reach Level 5",500, level>=5),
        ]
        for icon, title, desc, pts, unlocked in achievements:
            opacity = "1" if unlocked else "0.35"
            border = "border-left:3px solid #0EA5E9;" if unlocked else ""
            st.markdown(f"""
            <div class="ach" style="opacity:{opacity};{border}">
                <div class="ach-icon">{icon}</div>
                <div style="flex:1">
                    <div class="ach-text">{title}</div>
                    <div style="font-size:11px;color:#94A3B8">{desc}</div>
                </div>
                <div class="ach-pts">+{pts} XP</div>
            </div>
            """, unsafe_allow_html=True)

    with col_lb:
        st.markdown("##### 🥇 Community Leaderboard")

        leaderboard = [
            ("RK","Rahul K.", 1240, "#EFF6FF","#0369A1","🥇"),
            ("PM","Priya M.", 980, "#FFFBEB","#92400E","🥈"),
            ("AS","Amit S.",  760, "#FEF2F2","#991B1B","🥉"),
            ("DJ","Deepa J.", 550, "#F0F9FF","#0369A1","4"),
            ("VB","Vikram B.",430, "#F5F3FF","#6D28D9","5"),
        ]
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        for initials, name, pts, bg, fg, rank in leaderboard:
            st.markdown(f"""
            <div class="lb-row">
                <div class="lb-rank">{rank}</div>
                <div class="lb-avatar" style="background:{bg};color:{fg}">{initials}</div>
                <div class="lb-name">{name}</div>
                <div class="lb-pts">{pts:,} XP</div>
            </div>
            """, unsafe_allow_html=True)
        if xp > 0:
            st.markdown(f"""
            <div class="lb-row" style="background:#F0FDF4;border-radius:8px;padding:10px;margin-top:6px">
                <div class="lb-rank" style="color:#0EA5E9">You</div>
                <div class="lb-avatar" style="background:#EFF6FF;color:#0369A1">Y</div>
                <div class="lb-name" style="color:#0EA5E9;font-weight:600">You</div>
                <div class="lb-pts">{xp:,} XP</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # XP guide
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown("##### 💡 How to Earn XP")
        xp_actions = [("📸","Submit a report","+50 XP"),("👍","Verify a report","+10 XP"),("✅","Report gets resolved","+100 XP"),("🔥","3-day reporting streak","+150 XP"),("🏆","Reach new level","Bonus XP")]
        for icon, action, pts in xp_actions:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #F1F5F9;font-size:13px">
                <span style="font-size:18px">{icon}</span>
                <span style="flex:1;color:#334155">{action}</span>
                <span style="font-weight:700;color:#0EA5E9">{pts}</span>
            </div>
            """, unsafe_allow_html=True)


# ──────────────────────────────────────────
# PAGE: ABOUT
# ──────────────────────────────────────────
elif st.session_state.page == "About":
    st.markdown('<div class="sec-title"> About Community Hero</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">**AI-powered civic intelligence platform built for Real life Challenges**</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ###  Problem We Solve
        Communities across India face daily challenges — potholes, waterlogging, broken streetlights, overflowing garbage — yet reporting these issues is fragmented, untracked, and opaque.

        **Community Hero** transforms this by giving every citizen a powerful, AI-backed tool to detect, report, verify, and track civic issues — creating accountability and real change.

        ###  How Gemini AI Powers It
        - **Gemini 2.5 Flash Vision** — analyzes uploaded images to detect issue type, assess severity, and identify risk
        - **Structured JSON output** — returns precise categorization for dashboard analytics
        - **Complaint generation** — drafts formal letters to the appropriate municipal authority in seconds
        - **Predictive insights** — analyzes patterns across reports to surface hotspots
        """)

    with col2:
        st.markdown("""
        ###  Tech Stack
        | Layer | Technology |
        |-------|-----------|
        | AI Model | Google Gemini 2.5 Flash |
        | Framework | Streamlit |
        | Deployment | Streamlit |
        | Maps | Plotly Mapbox |
        | Charts | Plotly Express |
        | Storage | JSON (extensible to Firestore) |

        ###  Evaluation Alignment
        | Criterion | Implementation |
        |-----------|----------------|
        | Problem Solving | Civic issue lifecycle |
        | Agentic Depth | Multi-step AI pipeline |
        | Innovation | Vision + NLP + Gamification |
        | Google Tech | Gemini 2.5 Flash |
        | Product Design | Full UX with leaderboard |
        """)

    st.markdown("---")
    st.info(" Built for **Socities** — Community Hero Problem Statement")