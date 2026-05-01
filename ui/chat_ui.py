"""Clinexa AI · Appointment Booking — Agentic UI · JillaniSofTech"""

import uuid
from datetime import datetime
import streamlit as st
from agents.booking_agent import create_initial_state, process_message
from data.db import init_db, get_all_doctors, get_bookings_by_doctor_and_date

STAGES = {
    "greeting":          {"label": "Welcome",      "icon": "👋", "step": 0},
    "select_speciality": {"label": "Speciality",   "icon": "🩺", "step": 1},
    "select_doctor":     {"label": "Doctor",       "icon": "👨‍⚕️","step": 2},
    "select_date":       {"label": "Date",         "icon": "📅", "step": 3},
    "select_slot":       {"label": "Time Slot",    "icon": "⏰", "step": 4},
    "confirm":           {"label": "Review",       "icon": "📋", "step": 5},
    "collect_details":   {"label": "Your Details", "icon": "✍️", "step": 6},
    "completed":         {"label": "Confirmed",    "icon": "✅", "step": 7},
    "cancelled":         {"label": "Cancelled",    "icon": "❌", "step": 0},
}
TOTAL_STEPS = 7

# ── CSS ───────────────────────────────────────────────────────────────────────
def _css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    *, html, body {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #1a1a1a;
        color: #e8e8e8;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #111111 !important;
        border-right: 1px solid #2a2a2a !important;
    }

    section[data-testid="stSidebar"] * {
        color: #e8e8e8;
    }

    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    /* Keep Streamlit sidebar arrows working */
    button[kind="header"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    .main .block-container {
        max-width: 1400px !important;
        padding: 80px 60px 120px 60px !important;
    }

    .sb-header {
        padding: 18px 16px 14px;
        border-bottom: 1px solid #2a2a2a;
    }

    .sb-brand {
        font-size: 15px;
        font-weight: 700;
        color: #e8e8e8;
    }

    .sb-sub {
        font-size: 11px;
        color: #777;
        margin-top: 2px;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background: #1f1f1f !important;
        border: 1px solid #2f2f2f !important;
        color: #e8e8e8 !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 8px 12px !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #2a2a2a !important;
        border-color: #3a3a3a !important;
    }

    .doc-row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 16px;
        font-size: 12px;
        border-bottom: 1px solid #1a1a1a;
    }

    .doc-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .doc-dot.avail {
        background: #10a37f;
    }

    .doc-dot.busy {
        background: #555;
    }

    .doc-name {
        color: #ccc;
        font-weight: 600;
    }

    .doc-spec {
        font-size: 10px;
        color: #aaa;
    }

    .sb-section-title {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: .8px;
        color: #aaa;
        padding: 14px 16px 6px;
    }

    [data-testid="stChatInput"] {
        background: #242424 !important;
        border: 1px solid #333 !important;
        border-radius: 14px !important;
    }

    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: #e8e8e8 !important;
        font-size: 14px !important;
    }

    [data-testid="stChatInput"] button {
        background: #10a37f !important;
        border-radius: 8px !important;
    }

    .stage-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: #10a37f18;
        border: 1px solid #10a37f44;
        color: #10a37f;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
    }

    .brand-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #1a1a1a;
        border-top: 1px solid #2a2a2a;
        padding: 6px 0;
        font-size: 11px;
        color: #444;
        text-align: center;
        z-index: 9999;
    }

    .brand-footer a {
        color: #10a37f;
        text-decoration: none;
    }

    </style>
    """, unsafe_allow_html=True)


# ── Session ───────────────────────────────────────────────────────────────────
def _init():
    if "state"           not in st.session_state: st.session_state.state = create_initial_state()
    if "initialized"     not in st.session_state: st.session_state.initialized = False
    if "session_id"      not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
    if "processing"      not in st.session_state: st.session_state.processing = False
    if "past_sessions"   not in st.session_state: st.session_state.past_sessions = []
    if "viewing_session" not in st.session_state: st.session_state.viewing_session = None


def _save_session():
    state = st.session_state.state
    stage = state.get("stage")
    if stage not in ["completed", "cancelled"]:
        return
    sid = st.session_state.session_id
    if any(s["id"] == sid for s in st.session_state.past_sessions):
        return
    doctor = state.get("selected_doctor")
    bid    = state.get("booking_id")
    label  = (
        f"{doctor['doctor_name']} · {state.get('selected_date','')}" if bid
        else f"Cancelled · {state.get('selected_speciality') or 'N/A'}"
    )
    st.session_state.past_sessions.insert(0, {
        "id":         sid,
        "label":      label,
        "stage":      stage,
        "booking_id": bid,
        "messages":   list(state.get("messages", [])),
        "doctor":     doctor,
        "date":       state.get("selected_date"),
        "slot":       state.get("selected_slot"),
        "name":       state.get("customer_name"),
        "ts":         datetime.now().strftime("%b %d, %H:%M"),
    })


def _new_booking():
    _save_session()
    st.session_state.state = create_initial_state()
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.initialized = False
    st.session_state.viewing_session = None
    st.rerun()


# ── Doctor availability ───────────────────────────────────────────────────────
def _get_doctor_status(limit=8):
    """Return list of (doctor_name, speciality, is_available) for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        doctors = get_all_doctors()[:limit]
        result  = []
        for d in doctors:
            booked = get_bookings_by_doctor_and_date(d[0], today)
            # Simple heuristic: if all 4 slots booked → busy
            result.append((d[1], d[2], len(booked) < 4))
        return result
    except Exception:
        return []


# ── Sidebar ───────────────────────────────────────────────────────────────────
def _sidebar():
    state   = st.session_state.state
    stage   = state.get("stage", "greeting")
    cfg     = STAGES.get(stage, STAGES["greeting"])
    viewing = st.session_state.viewing_session

    with st.sidebar:
        # ── Brand header ──
        st.markdown("""
        <div class="sb-header">
            <div style="display:flex;align-items:center;gap:8px">
                <span style="font-size:22px">🏥</span>
                <div>
                    <div class="sb-brand">Clinexa AI</div>
                    <div class="sb-sub">by JillaniSofTech</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # ── New booking button ──
        st.markdown('<div style="padding:10px 10px 4px">', unsafe_allow_html=True)
        if st.button("＋  New Booking", use_container_width=True):
            _new_booking()
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Progress ──
        step = cfg["step"]
        st.markdown(
            f'<div style="padding:10px 0 2px;font-size:11px;color:#666;'
            f'display:flex;justify-content:space-between">'
            f'<span>{cfg["icon"]} {cfg["label"]}</span>'
            f'<span>{step}/{TOTAL_STEPS}</span></div>',
            unsafe_allow_html=True
        )
        st.progress(step / TOTAL_STEPS)
        st.markdown('<div style="margin-bottom:10px;border-bottom:1px solid #2a2a2a"></div>', unsafe_allow_html=True)

        # ── Current booking summary ──
        rows = []
        if state.get("selected_speciality"): rows.append(("🩺", state["selected_speciality"]))
        if state.get("selected_doctor"):     rows.append(("👨‍⚕️", state["selected_doctor"]["doctor_name"]))
        if state.get("selected_date"):       rows.append(("📅", state["selected_date"]))
        if state.get("selected_slot"):       rows.append(("⏰", state["selected_slot"]))
        if state.get("customer_name"):       rows.append(("🙋", state["customer_name"]))

        if rows:
            html = '<div class="bk-card">'
            for icon, val in rows:
                html += f'<div class="bk-row"><span class="bk-icon">{icon}</span><span class="bk-val">{val}</span></div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

        if state.get("booking_id"):
            st.markdown(f'<div class="bid-badge">✅ {state["booking_id"]}</div>', unsafe_allow_html=True)

        # ── Conversation history ──
        past = st.session_state.past_sessions
        if past:
            st.markdown('<div class="sb-section-title">Conversations</div>', unsafe_allow_html=True)
            for s in past[:10]:
                is_active = viewing == s["id"]
                icon = "✅" if s["stage"] == "completed" else "❌"
                active_style = "border-left:2px solid #10a37f;background:#1f1f1f;" if is_active else ""
                if st.button(
                    f"{icon} {s['label']}",
                    key=f"sess_{s['id']}",
                    use_container_width=True,
                    help=s.get("ts", "")
                ):
                    st.session_state.viewing_session = None if is_active else s["id"]
                    st.rerun()

        # ── Doctor availability ──
        doctors = _get_doctor_status(limit=8)
        if doctors:
            st.markdown('<div class="sb-section-title">Doctors Today</div>', unsafe_allow_html=True)
            html = ""
            for name, spec, avail in doctors:
                dot   = "avail" if avail else "busy"
                label = "Available" if avail else "Busy"
                html += (
                    f'<div class="doc-row">'
                    f'<div class="doc-dot {dot}" title="{label}"></div>'
                    f'<div><div class="doc-name">{name}</div>'
                    f'<div class="doc-spec">{spec}</div></div>'
                    f'</div>'
                )
            st.markdown(html, unsafe_allow_html=True)

        # ── Footer links ──
        st.markdown("""
        <div style="padding:16px 16px 10px;font-size:11px;color:#444;border-top:1px solid #2a2a2a;margin-top:10px">
            <a href="https://jillanisoftech.com/" target="_blank" style="color:#555;text-decoration:none">🌐 jillanisoftech.com</a><br>
            <a href="https://www.linkedin.com/in/jillanisofttech/" target="_blank" style="color:#555;text-decoration:none">💼 LinkedIn</a>
        </div>""", unsafe_allow_html=True)


# ── Chat ──────────────────────────────────────────────────────────────────────
def _chat():
    viewing_id = st.session_state.viewing_session

    # ── Viewing a past session ──
    if viewing_id:
        past_map = {s["id"]: s for s in st.session_state.past_sessions}
        if viewing_id in past_map:
            s = past_map[viewing_id]
            st.markdown(
                f'<div class="view-banner">📂 Viewing past session — {s["label"]} &nbsp;'
                f'<span style="color:#555">({s.get("ts","")})</span></div>',
                unsafe_allow_html=True
            )
            for msg in s["messages"]:
                with st.chat_message(msg["role"], avatar="🏥" if msg["role"]=="assistant" else None):
                    st.markdown(msg["content"])
            return

    # ── Live session ──
    messages = st.session_state.state.get("messages", [])
    stage    = st.session_state.state.get("stage", "greeting")

    if not messages:
        st.markdown("""
        <div class="empty-state">
            <div class="ico">🏥</div>
            <h3>Clinexa AI</h3>
            <p style="font-size:13px;margin-top:6px">Starting session…</p>
        </div>""", unsafe_allow_html=True)
        return

    for i, msg in enumerate(messages):
        is_last = i == len(messages) - 1
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🏥"):
                st.markdown(msg["content"])
                opts = msg.get("options", [])
                if opts and is_last and stage not in ["completed", "cancelled"]:
                    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
                    cols = st.columns(min(len(opts), 4))
                    for j, opt in enumerate(opts):
                        with cols[j % min(len(opts), 4)]:
                            if st.button(opt, key=f"opt_{i}_{j}"):
                                _send(opt)
                elif opts:
                    chips = " ".join(
                        f'<code style="background:#222;padding:2px 8px;border-radius:10px;'
                        f'color:#555;font-size:11px">{o}</code>' for o in opts
                    )
                    st.markdown(f'<div style="margin-top:4px">{chips}</div>', unsafe_allow_html=True)
        else:
            with st.chat_message("user", avatar=None):
                st.markdown(msg["content"])

    if st.session_state.processing:
        with st.chat_message("assistant", avatar="🏥"):
            st.markdown('<span class="dot"></span><span class="dot"></span><span class="dot"></span>', unsafe_allow_html=True)


# ── Input ─────────────────────────────────────────────────────────────────────
def _send(text: str):
    st.session_state.viewing_session = None
    st.session_state.processing = True
    st.session_state.state = process_message(
        st.session_state.state, text,
        thread_id=st.session_state.session_id
    )
    st.session_state.processing = False
    _save_session()
    st.rerun()


# ── Entry ─────────────────────────────────────────────────────────────────────
def run_chat_ui():
    st.set_page_config(
        page_title="Clinexa AI | JillaniSofTech",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={"About": "Clinexa AI v1.0 — JillaniSofTech"}
    )
    _css()
    init_db()
    _init()
    _sidebar()

    # Top bar
    c1, c2 = st.columns([5, 1])
    with c1:
        viewing = st.session_state.viewing_session
        if viewing:
            past_map = {s["id"]: s for s in st.session_state.past_sessions}
            label = past_map.get(viewing, {}).get("label", "Past Session")
            st.markdown(f'<div style="padding:14px 0 0;font-size:15px;font-weight:600;color:#888">📂 {label}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="padding:14px 0 0;font-size:15px;font-weight:600;color:#e8e8e8">Clinexa AI <span style="font-size:13px;color:#555;font-weight:400">· Appointment Booking</span></div>', unsafe_allow_html=True)
    with c2:
        stage = st.session_state.state.get("stage", "greeting")
        cfg   = STAGES.get(stage, STAGES["greeting"])
        st.markdown(f'<div style="text-align:right;padding-top:16px"><span class="stage-badge">{cfg["icon"]}&nbsp;{cfg["label"]}</span></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Boot
    if not st.session_state.initialized:
        st.session_state.state = process_message(
            st.session_state.state, "Hi",
            thread_id=st.session_state.session_id
        )
        st.session_state.initialized = True
        st.rerun()

    _chat()

    stage = st.session_state.state.get("stage", "greeting")
    viewing = st.session_state.viewing_session
    if not viewing and stage not in ["completed", "cancelled"]:
        if prompt := st.chat_input("Message Clinexa AI…"):
            _send(prompt)

    st.markdown("""
    <div class="brand-footer">
        <a href="https://jillanisoftech.com/" target="_blank">JillaniSofTech</a>
        &nbsp;·&nbsp; Clinexa AI v1.0
        &nbsp;·&nbsp;
        <a href="https://www.linkedin.com/in/jillanisofttech/" target="_blank">LinkedIn</a>
    </div>""", unsafe_allow_html=True)