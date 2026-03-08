"""
Phase 8 — Frontend: Apple macOS-inspired chatbot UI.

Layout (matching architecture.md §8.2):
  ┌─────────────────┬──────────────────────────────────┐
  │  Chat History    │        Chat Interface            │
  │  (Sidebar)       │  [Fund dropdown ▾] [✕ Clear]     │
  │                  │  Messages …                      │
  │                  │  [Ask about Quant Mutual Funds…]  │
  └─────────────────┴──────────────────────────────────┘

Features:
  - Conversation history with switching (§8.3)
  - Inline fund dropdown fetched from GET /mutual-funds (§8.4)
  - Fund context memory per conversation (§8.5)
  - POST /query with {query, active_fund, conversation_id} (§8.6)
  - Apple macOS design language (§8.7)
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st
import uuid
from datetime import datetime

from phase8_frontend.api_client import send_query, fetch_mutual_funds, fetch_last_updated
from phase8_frontend.config import get_sample_questions

st.set_page_config(
    page_title="Mutual Fund RAG Chatbot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS: Apple macOS aesthetic ──────────────────────────────────────

st.markdown("""
<style>
    /* ── Typography: system font stack ── */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
                     "Helvetica Neue", Arial, sans-serif;
    }

    /* ── Main area: full-width, clean white ── */
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100% !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff;
    }
    [data-testid="stHeader"] {
        background-color: #ffffff;
    }

    /* ── Header bar ── */
    .app-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 0;
        margin-bottom: 4px;
        border-bottom: 1px solid #e5e5e7;
    }
    .app-header-icon {
        font-size: 1.4rem;
    }
    .app-header-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1d1d1f;
        letter-spacing: -0.01em;
    }

    /* ── Sidebar: frosted-glass light gray ── */
    [data-testid="stSidebar"] {
        background-color: #f5f5f7;
        border-right: 1px solid #d2d2d7;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        color: #1d1d1f !important;
        font-size: 0.88rem;
    }
    [data-testid="stSidebar"] .stCaption {
        color: #86868b !important;
    }
    [data-testid="stSidebar"] input {
        background-color: #ffffff !important;
        border: 1px solid #d2d2d7 !important;
        border-radius: 8px !important;
        color: #1d1d1f !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        justify-content: flex-start;
        text-align: left;
        background-color: transparent !important;
        color: #1d1d1f !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        padding: 0.4rem 0.6rem !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #e8e8ed !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #007AFF !important;
        color: #ffffff !important;
        font-weight: 500;
        border-radius: 10px !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background-color: #0066d6 !important;
    }

    /* ── Chat messages ── */
    [data-testid="stChatMessage"] {
        padding: 0.4rem 0;
    }

    /* ── Fund dropdown row ── */
    .fund-bar {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 14px;
        margin-bottom: 12px;
        background: #f5f5f7;
        border: 1px solid #e5e5e7;
        border-radius: 12px;
        font-size: 0.85rem;
        color: #1d1d1f;
    }
    .fund-bar-label {
        font-weight: 500;
        white-space: nowrap;
        color: #86868b;
    }
    .fund-bar-name {
        font-weight: 600;
        color: #007AFF;
    }

    /* ── Welcome area ── */
    .welcome-title {
        font-size: 1.6rem;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }
    .welcome-sub {
        color: #86868b;
        font-size: 0.92rem;
        margin-bottom: 1.4rem;
        line-height: 1.55;
    }

    /* ── Sample question buttons ── */
    .stButton > button {
        border-radius: 10px !important;
        font-size: 0.85rem !important;
        transition: background-color 0.15s ease;
    }

    /* ── Chat input ── */
    [data-testid="stChatInput"] {
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    /* ── Selectbox (fund dropdown) ── */
    [data-testid="stSelectbox"] > div > div {
        border-radius: 10px !important;
        border-color: #d2d2d7 !important;
        font-size: 0.85rem !important;
    }

    /* ── Divider ── */
    hr {
        border-color: #e5e5e7 !important;
    }

    /* ── Responsive: mobile ── */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }
        .app-header-title { font-size: 1rem; }
        .welcome-title { font-size: 1.3rem; }
        .welcome-sub { font-size: 0.85rem; }
        [data-testid="stSidebar"] { min-width: 220px !important; }
    }

    /* ── Responsive: tablet ── */
    @media (min-width: 769px) and (max-width: 1024px) {
        .block-container {
            padding-left: 1.25rem;
            padding-right: 1.25rem;
        }
    }

    /* ── Responsive: large desktop ── */
    @media (min-width: 1400px) {
        .block-container {
            padding-left: 3rem;
            padding-right: 3rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="app-header">'
    '<span class="app-header-icon">📊</span>'
    '<span class="app-header-title">Mutual Fund RAG Chatbot</span>'
    '</div>',
    unsafe_allow_html=True,
)


# ── Session state initialisation ──────────────────────────────────────────

def _init_state():
    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    if "current_id" not in st.session_state:
        st.session_state.current_id = None
    if "history_search" not in st.session_state:
        st.session_state.history_search = ""
    if "sample_questions" not in st.session_state:
        st.session_state.sample_questions = get_sample_questions()
    if "fund_list" not in st.session_state:
        st.session_state.fund_list = []
    if "fund_list_error" not in st.session_state:
        st.session_state.fund_list_error = None
    if "last_updated" not in st.session_state:
        st.session_state.last_updated = None

_init_state()


# ── Helpers ───────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _ensure_conversation() -> str:
    if st.session_state.current_id is None or st.session_state.current_id not in st.session_state.conversations:
        cid = str(uuid.uuid4())[:8]
        st.session_state.conversations[cid] = {
            "conversation_id": cid,
            "title": "New chat",
            "messages": [],
            "active_fund": None,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        st.session_state.current_id = cid
    return st.session_state.current_id


def _add_message(role: str, content: str, citations: list[str] | None = None):
    cid = _ensure_conversation()
    conv = st.session_state.conversations[cid]
    conv["messages"].append({
        "id": str(uuid.uuid4())[:8],
        "role": role,
        "content": content,
        "citations": citations or [],
        "created_at": _now_iso(),
    })
    conv["updated_at"] = _now_iso()
    if role == "user" and conv["title"] == "New chat":
        conv["title"] = (content[:42] + "…") if len(content) > 42 else content


def _get_active_fund() -> str | None:
    cid = st.session_state.current_id
    if cid and cid in st.session_state.conversations:
        return st.session_state.conversations[cid].get("active_fund")
    return None


def _set_active_fund(fund_name: str | None):
    cid = _ensure_conversation()
    st.session_state.conversations[cid]["active_fund"] = fund_name
    st.session_state.conversations[cid]["updated_at"] = _now_iso()


def _run_query(text: str):
    if not text or not text.strip():
        return
    _add_message("user", text.strip())
    cid = st.session_state.current_id
    active = _get_active_fund()
    result = send_query(text.strip(), active_fund=active, conversation_id=cid)
    if result.get("error"):
        _add_message("assistant", f"⚠️ {result['error']}", [])
    else:
        _add_message("assistant", result["answer"], result.get("citations", []))


def _load_fund_list():
    if not st.session_state.fund_list:
        result = fetch_mutual_funds()
        if result["error"]:
            st.session_state.fund_list_error = result["error"]
        else:
            st.session_state.fund_list = result["funds"]
            st.session_state.fund_list_error = None


def _load_last_updated():
    if st.session_state.last_updated is None:
        result = fetch_last_updated()
        st.session_state.last_updated = result


def _format_last_updated(short: bool = False) -> str:
    info = st.session_state.last_updated
    if not info or info.get("status") == "never_run":
        return "Data not yet refreshed"
    ts = info.get("last_updated_ist") or info.get("last_updated_utc")
    if not ts:
        return "Data not yet refreshed"
    try:
        from datetime import datetime as _dt
        dt = _dt.fromisoformat(ts)
        if short:
            return dt.strftime("%d %b %Y")
        return dt.strftime("%d %b %Y, %I:%M %p IST")
    except Exception:
        return ts


# ── SIDEBAR: Conversation History ─────────────────────────────────────────

_load_last_updated()

with st.sidebar:
    st.markdown("### 📊 Quant MF Facts")
    st.caption("Facts-only assistant for Quant Mutual Funds")
    st.caption(f"Data last refreshed: {_format_last_updated()}")
    st.divider()

    if st.button("New Chat", use_container_width=True, type="primary"):
        st.session_state.current_id = None
        st.session_state.sample_questions = get_sample_questions()
        st.rerun()

    st.markdown("**Conversations**")
    search = st.text_input(
        "Search conversations",
        value=st.session_state.history_search,
        placeholder="Search…",
        key="sidebar_search",
        label_visibility="collapsed",
    )
    st.session_state.history_search = (search or "").strip().lower()

    conv_ids = [
        cid for cid in st.session_state.conversations
        if st.session_state.conversations[cid]["messages"]
    ]
    conv_ids.sort(key=lambda c: st.session_state.conversations[c].get("updated_at", ""), reverse=True)

    if st.session_state.history_search:
        conv_ids = [
            cid for cid in conv_ids
            if st.session_state.history_search in (st.session_state.conversations[cid].get("title") or "").lower()
        ]

    if not conv_ids:
        st.caption("No conversations yet" if not st.session_state.history_search else "No matches")
    for cid in conv_ids:
        conv = st.session_state.conversations[cid]
        title = conv.get("title") or "New chat"
        fund_tag = f" · {conv['active_fund']}" if conv.get("active_fund") else ""
        label = f"{title}{fund_tag}"
        is_current = cid == st.session_state.current_id
        if st.button(label, key=f"conv_{cid}", use_container_width=True, disabled=is_current):
            st.session_state.current_id = cid
            st.rerun()


# ── MAIN AREA: Fund Dropdown + Chat Interface ────────────────────────────

_load_fund_list()

# Fund dropdown
fund_options = ["No fund selected"] + st.session_state.fund_list
current_active = _get_active_fund()
current_index = 0
if current_active and current_active in fund_options:
    current_index = fund_options.index(current_active)

col_dd, col_clear = st.columns([4, 1])
with col_dd:
    selected = st.selectbox(
        "Select a mutual fund",
        options=fund_options,
        index=current_index,
        key="fund_dropdown",
        label_visibility="collapsed",
    )
with col_clear:
    if current_active:
        if st.button("✕ Clear", key="clear_fund", use_container_width=True):
            _set_active_fund(None)
            st.rerun()

if selected and selected != "No fund selected":
    if selected != current_active:
        _set_active_fund(selected)
elif current_active:
    _set_active_fund(None)

# Show active fund indicator
active = _get_active_fund()
if active:
    st.markdown(
        f'<div class="fund-bar"><span class="fund-bar-label">Active Fund:</span> '
        f'<span class="fund-bar-name">{active}</span></div>',
        unsafe_allow_html=True,
    )

# Chat area
is_new_chat = st.session_state.current_id is None or (
    st.session_state.current_id in st.session_state.conversations
    and not st.session_state.conversations[st.session_state.current_id]["messages"]
)

if is_new_chat:
    st.markdown('<p class="welcome-title">What would you like to know?</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="welcome-sub">Ask factual questions about Quant Mutual Funds — '
        'NAV, expense ratio, holdings, fund managers, and more. '
        'Select a fund from the dropdown above, or mention it in your question.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("**Try asking:**")
    for sq in st.session_state.sample_questions:
        if st.button(sq, key=f"sq_{sq[:20]}", use_container_width=True):
            _run_query(sq)
            st.rerun()
    st.caption("📌 Facts-only. No investment advice.")
else:
    conv = st.session_state.conversations[st.session_state.current_id]
    last_updated_short = _format_last_updated(short=True)
    for m in conv["messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant" and m.get("citations"):
                for url in m["citations"]:
                    st.caption(f"[Source]({url})  ·  Last updated: {last_updated_short}")

prompt = st.chat_input("Ask about Quant Mutual Funds…")
if prompt:
    _run_query(prompt)
    st.rerun()

# Auto-scroll to bottom when conversation has messages
if not is_new_chat:
    st.markdown(
        '<script>window.parent.document.querySelector("section.main").scrollTo(0, 999999);</script>',
        unsafe_allow_html=True,
    )
