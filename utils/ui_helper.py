import streamlit as st
import streamlit.components.v1 as components
import json
from datetime import datetime
from utils import storage

# st_autorefresh removed in favor of native query_params


def apply_navbar_fix(active_page, pages):
    """
    Applies global CSS and JS for the EduAI navigation system.
    Consolidates sidebar, navbar, and general UI styling.
    """
    if not pages:
        st.markdown("""
        <style>
        #MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stSidebarNav"] { display: none !important; }
        </style>
        """, unsafe_allow_html=True)
        return

    st.markdown("""
    <style>
    /* 1. Global Hiding & Layout */
    #MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stHeader"] {
        background: transparent !important;
        z-index: 10000 !important;
        pointer-events: none !important;
        height: 70px !important;
    }
    [data-testid="stHeader"] * { pointer-events: auto !important; }
    [data-testid="stAppViewBlockContainer"] { padding-top: 85px !important; }

    /* 2. Custom Navbar Styling */
    #eduai-nav-block {
        position: fixed !important;
        top: 0 !important; left: 0 !important; right: 0 !important;
        height: 70px !important; z-index: 9999 !important;
        background: #0d1117 !important;
        border-bottom: 2px solid rgba(255,255,255,0.1) !important;
        padding: 0 40px 0 60px !important; margin: 0 !important;
        display: flex !important; align-items: center !important;
    }
    .eduai-logo {
        font-size: 1.15rem !important; font-weight: 800 !important;
        background: linear-gradient(135deg, #6366f1, #a855f7) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        white-space: nowrap !important; margin-right: auto !important;
    }

    /* 3. Sidebar Customization */
    section[data-testid="stSidebar"] {
        top: 70px !important;
        height: calc(100vh - 70px) !important;
        background: rgba(13,17,23,0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
    }
    /* Hide native collapse headers */
    [data-testid="stSidebar"] [data-testid="stSidebarHeader"],
    [data-testid="stSidebar"] button[kind="header"],
    button[aria-label="Close sidebar"] {
        display: none !important;
    }

    /* Floating Re-open Control */
    [data-testid="collapsedControl"],
    button[aria-label="Open sidebar"],
    [data-testid="stSidebarCollapsedControl"] {
        background: rgba(30,41,59,0.95) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 10px !important;
        position: fixed !important;
        top: 85px !important;
        left: 15px !important;
        z-index: 100001 !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        width: 42px !important;
        height: 42px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* 4. Unified Choice Box Styling */
    .eduai-choice-box {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        margin: 10px 0 20px 55px !important;
        width: fit-content !important;
        min-width: 320px !important;
        max-width: 500px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    }
    .eduai-choice-header {
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: rgba(255, 255, 255, 0.4) !important;
        margin: 0 0 15px 0 !important;
        font-weight: 600 !important;
        text-align: center !important;
    }
    .stButton > button.eduai-choice {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        transition: all 0.25s ease !important;
        width: 100% !important;
        margin: 0 0 8px 0 !important;
        text-align: center !important;
        white-space: nowrap !important;
    }

    /* Navbar Button Fix */
    #eduai-nav-block button {
        white-space: nowrap !important;
        padding: 0 12px !important;
        font-size: 0.85rem !important;
        height: 38px !important;
        min-width: fit-content !important;
    }

    /* 5. Jump to Bottom Button (EduAI Premium) */
    #eduai-jump-btn {
        position: fixed !important;
        bottom: 100px !important;
        right: 40px !important;
        background: linear-gradient(135deg, #6366f1, #a855f7) !important;
        color: white !important;
        width: 46px !important;
        height: 46px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        z-index: 999999 !important;
        opacity: 0 !important;
        visibility: hidden !important;
        transform: scale(0.8) translateY(20px) !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 10px 25px rgba(99, 102, 241, 0.4) !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        font-size: 1.2rem !important;
        line-height: 1 !important;
        padding-bottom: 2px !important;
    }
    #eduai-jump-btn.visible {
        opacity: 1 !important;
        visibility: visible !important;
        transform: scale(1) translateY(0) !important;
        animation: eduai-pulse 2s infinite !important;
    }
    @keyframes eduai-pulse {
        0% { box-shadow: 0 10px 25px rgba(99, 102, 241, 0.4); }
        50% { box-shadow: 0 10px 35px rgba(168, 85, 247, 0.7); }
        100% { box-shadow: 0 10px 25px rgba(99, 102, 241, 0.4); }
    }
    #eduai-jump-btn:hover {
        transform: scale(1.1) translateY(-5px) !important;
        box-shadow: 0 15px 30px rgba(168, 85, 247, 0.5) !important;
        animation: none !important;
    }

    /* 6. Premium Components (Timer & Mission) */
    .eduai-mission-card {
        background: rgba(30, 41, 59, 0.45) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        padding: 24px !important;
        margin: 20px 0 !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4) !important;
    }
    .eduai-timer-hero {
        font-family: 'Inter', monospace !important;
        font-weight: 800 !important;
        text-align: center !important;
        background: linear-gradient(135deg, #ffffff, #6366f1);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        filter: drop-shadow(0 0 15px rgba(99, 102, 241, 0.3));
        margin: 10px 0 !important;
    }
    .eduai-timer-paused {
        color: #f59e0b !important;
        background: none !important;
        -webkit-text-fill-color: #f59e0b !important;
        filter: drop-shadow(0 0 10px rgba(245, 158, 11, 0.4));
    }
    .eduai-session-badge {
        background: rgba(99, 102, 241, 0.1) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 12px !important;
        padding: 8px 12px !important;
        margin-bottom: 8px !important;
        font-size: 0.85rem !important;
        transition: all 0.3s ease !important;
    }
    .eduai-session-badge:hover {
        background: rgba(99, 102, 241, 0.2) !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
        transform: translateX(5px) !important;
    }
    .eduai-session-row {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 12px 20px !important;
        margin-bottom: 12px !important;
        transition: all 0.3s ease !important;
    }
    .eduai-session-row:hover {
        background: rgba(255, 255, 255, 0.06) !important;
        border-color: rgba(99, 102, 241, 0.3) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
    }
    .eduai-trash-btn {
        color: #ef4444 !important;
        cursor: pointer !important;
        opacity: 0.6 !important;
        transition: all 0.2s ease !important;
    }
    .eduai-trash-btn:hover {
        opacity: 1 !important;
        transform: scale(1.2) !important;
    }
    .eduai-mission-control {
        position: fixed !important;
        top: 80px !important;
        right: 20px !important;
        width: 260px !important;
        z-index: 1000 !important;
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(20px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 20px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
    }

    /* 7. Scrollbars */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.5); border-radius: 10px; }

    /* 8. Visual Roadmap Pathway */
    .roadmap-container {
        padding: 40px 20px !important;
        position: relative !important;
        max-width: 900px !important;
        margin: 0 auto !important;
    }
    .roadmap-pathway {
        position: absolute !important;
        left: 45px !important;
        top: 60px !important;
        bottom: 60px !important;
        width: 3px !important;
        background: linear-gradient(to bottom, #6366f1, #a855f7, rgba(168, 85, 247, 0.1)) !important;
        z-index: 1 !important;
        border-radius: 4px !important;
    }
    .roadmap-week-section {
        position: relative !important;
        margin-bottom: 50px !important;
        z-index: 2 !important;
    }
    .roadmap-week-node {
        position: absolute !important;
        left: 31px !important;
        top: 0 !important;
        width: 32px !important;
        height: 32px !important;
        background: #0f172a !important;
        border: 3px solid #6366f1 !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.5) !important;
        z-index: 3 !important;
    }
    .roadmap-card {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        margin-left: 80px !important;
        padding: 24px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
    }
    .roadmap-card:hover {
        transform: translateY(-5px) !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4) !important;
        background: rgba(30, 41, 59, 0.55) !important;
    }
    .roadmap-week-title {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        margin-bottom: 15px !important;
        background: linear-gradient(135deg, #ffffff, #94a3b8) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }
    .roadmap-day-item {
        margin-bottom: 20px !important;
        padding-left: 15px !important;
        border-left: 2px solid rgba(99, 102, 241, 0.2) !important;
    }
    .roadmap-day-title {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #e2e8f0 !important;
        margin-bottom: 8px !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }
    .roadmap-task-pill {
        display: inline-block !important;
        background: rgba(99, 102, 241, 0.1) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 10px !important;
        padding: 6px 12px !important;
        margin: 4px 4px 4px 0 !important;
        font-size: 0.85rem !important;
        color: #cbd5e1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    components.html("""
    <script>
    (function() {
        var pdoc = window.parent.document;
        
        // Tag the navbar block
        function tagNavBlock() {
            var blocks = pdoc.querySelectorAll('[data-testid="stHorizontalBlock"]');
            if (blocks.length > 0) {
                blocks[0].id = 'eduai-nav-block';
            } else {
                setTimeout(tagNavBlock, 100);
            }
        }
        tagNavBlock();

        // Auto-expand sidebar
        function autoExpandSidebar() {
            try {
                var keys = Object.keys(window.parent.localStorage);
                for (var i = 0; i < keys.length; i++) {
                    if (keys[i].includes('stSidebarCollapsed')) {
                        window.parent.localStorage.setItem(keys[i], 'false');
                    }
                }
            } catch (e) {}

            var btn = pdoc.querySelector('button[aria-label="Open sidebar"]') || 
                      pdoc.querySelector('[data-testid="collapsedControl"]') ||
                      pdoc.querySelector('section[data-testid="stHeader"] button');
            
            if (btn && btn.offsetParent !== null) {
                btn.click();
            }
        }
        setTimeout(autoExpandSidebar, 500);
    })();
    </script>
    """, height=0)


def render_nav_buttons(active_page, pages):
    logo_col, *page_cols = st.columns([3] + [1] * len(pages))
    with logo_col:
        st.markdown('<div class="eduai-logo">EDUAI&nbsp;|</div>', unsafe_allow_html=True)
    for pg, col in zip(pages, page_cols):
        btn_type = "primary" if pg == active_page else "secondary"
        if col.button(pg, key=f"nav_btn_{pg}", use_container_width=True, type=btn_type):
            if pg != active_page:
                st.session_state.page = pg
                st.session_state.pop("nav_radio", None)
                st.rerun()

def render_sidebar_branding():
    st.markdown("""
    <div style="padding: 10px 0 20px 0;">
        <div style="font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 1.6rem; display: flex; align-items: center; gap: 8px; margin-bottom: 0;">
            <span style="background: linear-gradient(135deg, #6366f1, #a855f7);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                EDUAI
            </span>
            <span style="-webkit-text-fill-color: initial;">🧠</span>
        </div>
        <div style="font-size: 0.85rem; color: #9ca3af; margin-top: -5px; font-weight: 500;">
            Your AI Study Companion
        </div>
        <div style="height: 1px; background: linear-gradient(90deg, rgba(99,102,241,0.3), transparent); 
                    margin: 15px 0;"></div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar_header(title, icon="📁"):
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;">
        <span style="font-size: 1.2rem; filter: drop-shadow(0 0 5px rgba(99,102,241,0.5));">{icon}</span>
        <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.1rem; 
                    background: linear-gradient(135deg, #6366f1, #a855f7);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{title}</div>
    </div>
    <div style="height: 1px; background: linear-gradient(90deg, rgba(99,102,241,0.5), transparent); margin-bottom: 16px;"></div>
    """, unsafe_allow_html=True)

def begin_sidebar_layout():
    if "sidebar_open" not in st.session_state:
        st.session_state.sidebar_open = True
    cols = st.columns([1.1, 3.9]) if st.session_state.sidebar_open else st.columns([0.15, 4.85])
    return cols[0], cols[1]

def render_sidebar_toggle():
    is_open = st.session_state.get("sidebar_open", True)
    icon, tooltip = ("<<" if is_open else ">>"), ("Collapse" if is_open else "Expand")
    if st.button(icon, key="sidebar_toggle_btn", help=tooltip):
        st.session_state.sidebar_open = not st.session_state.sidebar_open
        st.rerun()

def render_chips(options, key_prefix, title="Select an option"):
    selected = None
    st.markdown(f'<div id="choice-marker-{key_prefix}" style="display:none;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="eduai-choice-header" id="choice-header-{key_prefix}">{title}</div>', unsafe_allow_html=True)
    
    for i, opt in enumerate(options):
        if st.button(opt, key=f"{key_prefix}_{i}"):
            selected = opt
    
    js_options = json.dumps(options)
    components.html(f"""
    <script>
    (function() {{
        var pdoc = window.parent.document;
        var opts = {js_options};
        var btns = pdoc.querySelectorAll('button');
        btns.forEach(btn => {{
            if (opts.includes(btn.innerText.trim())) btn.classList.add('eduai-choice');
        }});

        function tagChoiceBox() {{
            var header = pdoc.getElementById('choice-header-{key_prefix}');
            if (header) {{
                var container = header.closest('[data-testid="stVerticalBlock"]');
                if (container && !container.classList.contains('eduai-choice-box')) {{
                    container.classList.add('eduai-choice-box');
                    container.querySelectorAll('.stButton').forEach(b => b.style.margin = "0");
                }}
            }} else {{ setTimeout(tagChoiceBox, 100); }}
        }}
        tagChoiceBox();
    }})();
    </script>
    """, height=0)
    return selected

def render_roadmap_visual(content):
    """
    Parses AI roadmap content into a premium visual pathway.
    Principle: Always store raw text/markdown, always render fresh HTML cards.
    """
    if not content: return
    
    import re

    # ── Step 0: Normalize & Strip ───────────────────────────────────────────
    # 1. Strip markdown code markers
    content = re.sub(r'```[a-z]*', '', content, flags=re.I)
    content = content.replace('```', '').strip()
    
    # 2. CRITICAL: Strip leading indentation from EVERY line.
    # Streamlit/Markdown treats lines starting with 4+ spaces as code blocks.
    content = "\n".join([line.strip() for line in content.split("\n")])

    def strip_html(text):
        # Unescape common HTML entities
        text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        # Replace block-level tags with newlines
        text = re.sub(r'<(div|p|li|br|h\d|section|header)[^>]*>', '\n', text, flags=re.I)
        text = re.sub(r'</(div|p|li|br|h\d|section|header|span)>', '\n', text, flags=re.I)
        # Remove all remaining tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove decorative symbols
        text = re.sub(r'[◈•►▸▷◆◇→⟶]', '', text)
        # Collapse excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    plain = strip_html(content)

    # ── Step 1: Structural Parsing ──────────────────────────────────────────
    weeks = []
    current_week = None
    current_day  = None
    
    # Track current state for sequential numbering
    day_counter = 0 

    for raw_line in plain.split('\n'):
        raw_line = raw_line.strip()
        if not raw_line: continue
        
        # Clean line for keyword matching (strip leading symbols/bullets)
        clean_line = re.sub(r'^[\-\*\•\►\▸\◈\s]+', '', raw_line).strip()
        clean_line = clean_line.replace('**', '').strip()

        # Detect Week header
        week_match = re.match(r'(Week|Mission)\s*(\d+)', clean_line, re.I)
        if week_match and len(clean_line) < 60:
            title = f"Week {week_match.group(2)}"
            current_week = {"title": title, "days": []}
            weeks.append(current_week)
            current_day = None
            day_counter = 0 # Reset for new week
            continue

        # Detect Day header
        day_match = re.match(r'Day\s*(\d+)', clean_line, re.I)
        if day_match and current_week is not None and len(clean_line) < 40:
            day_counter += 1
            if day_counter > 7: day_counter = 7 # Safety clamp
            
            current_day = {"title": f"Day {day_counter}", "tasks": []}
            current_week["days"].append(current_day)
            continue

        # Task detection (bullet points or numbered lists)
        is_task = clean_line.startswith('-') or clean_line.startswith('*') or re.match(r'^\d+\.', clean_line)
        if not is_task and (clean_line.lower().startswith('technical') or clean_line.lower().startswith('non-technical') or clean_line.lower().startswith('task')):
            is_task = True

        if is_task and current_week is not None:
            # If we see a task but haven't seen a day header yet, start Day 1
            if current_day is None:
                day_counter = 1
                current_day = {"title": "Day 1", "tasks": []}
                current_week["days"].append(current_day)
            
            task_text = re.sub(r'^(?:Task\s*\d+|Technical\s*Task|Non-Technical\s*Task)\s*:\s*', '', clean_line, flags=re.I).strip()
            if task_text and len(task_text) > 5:
                current_day["tasks"].append(task_text)

    # ── Step 2: Final Render (Single HTML Block) ────────────────────────────
    if not weeks:
        st.markdown(content, unsafe_allow_html=True)
        return

    full_html = '<div class="roadmap-container"><div class="roadmap-pathway"></div>'
    for week in weeks:
        days_html = ""
        for day in week["days"]:
            tasks_html = "".join(f'<div class="roadmap-task-pill">{t}</div>' for t in day["tasks"])
            days_html += f"""
<div class="roadmap-day-item">
<div class="roadmap-day-title"><span style="color:#a855f7;">◈</span> {day["title"]}</div>
<div class="roadmap-tasks">{tasks_html}</div>
</div>"""

        full_html += f"""
<div class="roadmap-week-section">
<div class="roadmap-week-node">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
<polyline points="20 6 9 17 4 12"></polyline>
</svg>
</div>
<div class="roadmap-card">
<div class="roadmap-week-title">{week["title"]}</div>
{days_html}
</div>
</div>"""
    
    full_html += '</div>'
    st.markdown(full_html, unsafe_allow_html=True)


def render_multi_chips(options, key_prefix, title="Select multiple"):
    """
    Renders chips that allow multiple selection with a grid layout.
    """
    if f"{key_prefix}_selected" not in st.session_state:
        st.session_state[f"{key_prefix}_selected"] = []
    
    st.markdown(f'<div class="eduai-choice-header">{title}</div>', unsafe_allow_html=True)
    
    # Use a grid layout (3 columns)
    cols_per_row = 3
    for i in range(0, len(options), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(options):
                opt = options[idx]
                is_selected = opt in st.session_state[f"{key_prefix}_selected"]
                btn_type = "primary" if is_selected else "secondary"
                if cols[j].button(opt, key=f"{key_prefix}_{idx}", type=btn_type, use_container_width=True):
                    if is_selected:
                        st.session_state[f"{key_prefix}_selected"].remove(opt)
                    else:
                        st.session_state[f"{key_prefix}_selected"].append(opt)
                    st.rerun()
    
    if st.session_state[f"{key_prefix}_selected"]:
        st.markdown('<div style="margin-top:15px;"></div>', unsafe_allow_html=True)
        if st.button("✅ Confirm Selection", key=f"{key_prefix}_confirm", type="primary", use_container_width=True):
            res = ", ".join(st.session_state[f"{key_prefix}_selected"])
            del st.session_state[f"{key_prefix}_selected"]
            return res
            
    return None

def render_focus_sync_background(user_id=None, planned_mins=25):
    """Receives heartbeat from eye_tracker JS and saves session on stop."""
    import streamlit.components.v1 as components

    # JS bridge — writes heartbeat postMessage to hidden input
    components.html("""
    <script>
    (function() {
        try {
            window.top.addEventListener('message', function(event) {
                if (!event.data || !event.data.type) return;
                const pdoc = window.top.document;

                if (event.data.type === 'focus_sync_heartbeat') {
                    const input = pdoc.querySelector('input[placeholder="SAMS_HEARTBEAT"]');
                    if (input) {
                        const newVal = JSON.stringify(event.data.data);
                        try {
                            const nativeSetter = Object.getOwnPropertyDescriptor(
                                window.HTMLInputElement.prototype, 'value'
                            ).set;
                            nativeSetter.call(input, newVal);
                        } catch(e) { input.value = newVal; }
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }

                if (event.data.type === 'focus_start') {
                    const input = pdoc.querySelector('input[placeholder="SAMS_START"]');
                    if (input) {
                        const newVal = 'START_' + event.data.startTime;
                        try {
                            const nativeSetter = Object.getOwnPropertyDescriptor(
                                window.HTMLInputElement.prototype, 'value'
                            ).set;
                            nativeSetter.call(input, newVal);
                        } catch(e) { input.value = newVal; }
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            });
        } catch(e) {}
    })();
    </script>
    """, height=0)

    st.markdown("""
        <style>
        div[data-testid="stTextInput"]:has(input[placeholder="SAMS_HEARTBEAT"]),
        div[data-testid="stTextInput"]:has(input[placeholder="SAMS_START"]) {
            position: fixed !important; top: -100px !important;
            opacity: 0 !important; pointer-events: none !important;
            height: 0 !important; width: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    raw_start = st.text_input("st", key="s_start_bg", label_visibility="collapsed", placeholder="SAMS_START")
    raw_beat  = st.text_input("hb", key="s_sync_bg",  label_visibility="collapsed", placeholder="SAMS_HEARTBEAT")

    if raw_start and "START_" in raw_start:
        try:
            st.session_state.eye_state["running"]    = True
            st.session_state.eye_state["start_time"] = int(raw_start.split("_")[1])
            st.session_state.start_time_iso          = datetime.now().isoformat()
        except: pass

    if not raw_beat or "{" not in raw_beat:
        return

    try:
        beat = json.loads(raw_beat)
        is_stopped_signal = beat.get('stopped', False)

        if is_stopped_signal:
            session_key = str(beat.get('startTime', ''))
            if session_key and session_key == st.session_state.get('last_saved_session_key', ''):
                return

            st.session_state.last_saved_session_key = session_key

            counts       = beat.get('counts', {})
            phone        = int(counts.get('phone', 0))
            drowsy       = int(counts.get('drowsy', 0))
            zone_out     = int(counts.get('zone_out', 0))
            pauses       = int(counts.get('pauses', 0))
            distractions = phone + drowsy + zone_out
            focus_score  = max(0, 100 - phone*5 - drowsy*5 - zone_out*5 - pauses*2)
            elapsed      = max(1, round(float(beat.get('elapsedMins', 1)), 1))

            task_id, task_note = None, 'General Focus Session'
            if user_id:
                try:
                    rm_id = st.session_state.get('current_roadmap_id')
                    rm    = storage.get_roadmap_by_id(user_id, rm_id) if rm_id else storage.get_latest_roadmap(user_id)
                    if rm:
                        tasks   = storage.get_tasks(user_id, rm['id'])
                        pending = [t for t in tasks if t['status'] == 'pending']
                        if pending:
                            task_id   = pending[0]['id']
                            task_note = pending[0]['description']
                except: pass

            if user_id:
                storage.save_session(user_id, {
                    "task_id":           task_id,
                    "start_time":        st.session_state.get('start_time_iso', datetime.now().isoformat()),
                    "end_time":          datetime.now().isoformat(),
                    "planned_duration":  int(planned_mins),
                    "actual_duration":   elapsed,
                    "focus_score":       int(focus_score),
                    "distraction_count": distractions,
                    "phone_count":       phone,
                    "drowsy_count":      drowsy,
                    "zone_out_count":    zone_out,
                    "pause_count":       pauses,
                    "notes":             f"Mission: {task_note}"
                })
                print(f"[SAVED] score={focus_score} phone={phone} drowsy={drowsy} zone={zone_out} mins={elapsed}")

            st.session_state.last_summary = {
                "score": int(focus_score), "distractions": distractions, "mins": elapsed
            }
            st.session_state.eye_state = {
                "running": False, "start_time": 0, "score": 100,
                "counts": {"phone": 0, "drowsy": 0, "zone_out": 0}
            }
            st.session_state.persistent_eye_state      = {}
            st.session_state.persistent_remaining_secs = 0
            st.rerun()

        else:
            st.session_state.eye_state.update({
                "running":        True,
                "isPaused":       beat.get('isPaused', False),
                "start_time":     beat.get('startTime', 0),
                "score":          beat.get('score', 100),
                "counts":         beat.get('counts', {}),
                "remaining_secs": beat.get('remaining_secs'),
                "fixed_duration": beat.get('fixed_duration'),
                "target_time":    beat.get('target_time')
            })
            st.session_state.persistent_eye_state      = st.session_state.eye_state.copy()
            st.session_state.persistent_remaining_secs = beat.get('remaining_secs', 0)

    except Exception as e:
        import traceback
        print(f"[HEARTBEAT ERROR] {traceback.format_exc()}")




def render_jump_to_bottom():
    """
    Renders a unified, scroll-aware floating button to jump to the bottom.
    Works on all pages without anchors.
    """
    # 1. Inject Button Structure
    st.markdown('<div id="eduai-jump-btn" title="Jump to bottom">⬇️</div>', unsafe_allow_html=True)

    # 2. Inject Performance Logic
    components.html("""
    <script>
    (function() {
        var pdoc = window.parent.document;
        var retryCount = 0;
        
        function initJumpBtn() {
            var container = pdoc.querySelector('[data-testid="stAppViewMain"]') || 
                            pdoc.querySelector('.stMain') || 
                            pdoc.querySelector('.main') || 
                            pdoc.querySelector('[data-testid="block-container"]');
            var btn = pdoc.getElementById('eduai-jump-btn');

            if (!container || !btn) {
                if (retryCount < 20) { 
                    retryCount++; 
                    setTimeout(initJumpBtn, 500); 
                }
                return;
            }

            function updateVisibility() {
                var scrollPos = container.scrollTop;
                var totalHeight = container.scrollHeight;
                var visibleHeight = container.clientHeight;
                var fromBottom = totalHeight - scrollPos - visibleHeight;

                // Lower threshold to 100px for better visibility
                if (scrollPos > 100 && fromBottom > 50) {
                    btn.classList.add('visible');
                } else {
                    btn.classList.remove('visible');
                }
            }

            container.addEventListener('scroll', updateVisibility, { passive: true });
            btn.onclick = function() {
                container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
            };
            
            // Periodic check in case Streamlit forces a layout shift
            setInterval(updateVisibility, 1000);
        }

        // Delay to ensure Streamlit DOM is ready
        setTimeout(initJumpBtn, 800);
    })();
    </script>
    """, height=0)

def render_daily_mission_navigator(user_id, current_week, current_day, 
                                   all_tasks, total_weeks):
    """
    Renders WEEK X • DAY Y with < and > navigation buttons.
    The > button is ALWAYS visible but locked when tasks incomplete.
    
    Args:
        user_id: for fetching tasks
        current_week: Week number (1-indexed)
        current_day: Day number (1-indexed)
        all_tasks: List of all tasks from storage
        total_weeks: Total weeks in the roadmap
    
    Returns:
        (new_week, new_day) if navigation happened, else (current_week, current_day)
    """
    import streamlit as st
    
    # Check if current day tasks are complete
    current_day_tasks = [
        t for t in all_tasks 
        if t['week'] == current_week and t['day'] == current_day
    ]
    is_complete = all(t['status'] == 'done' for t in current_day_tasks) if current_day_tasks else True
    
    # Layout: 3 columns [<] [WEEK X DAY Y] [>]
    col_prev, col_center, col_next = st.columns([1, 2, 1])
    
    # LEFT BUTTON: < (always clickable)
    with col_prev:
        if st.button("‹", key=f"nav_prev_{current_week}_{current_day}",
                     use_container_width=True, type="secondary"):
            if current_day > 1:
                return current_week, current_day - 1
            elif current_week > 1:
                # Find actual last day of previous week from data
                prev_week_days = [t['day'] for t in all_tasks if t['week'] == current_week - 1]
                last_day_prev = max(prev_week_days) if prev_week_days else 7
                return current_week - 1, last_day_prev
    
    # CENTER: Display current week and day
    with col_center:
        st.markdown(f"""
        <div style="text-align: center; padding: 6px 0; color: #cbd5e1; 
                    font-size: 0.85rem; font-weight: 700; letter-spacing: 0.5px;
                    display: flex; flex-direction: column; justify-content: center; height: 38px;">
            <div style="opacity: 0.7; font-size: 0.7rem;">WEEK {current_week}</div>
            <div>DAY {current_day}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # RIGHT BUTTON: > (always visible, locked/unlocked based on completion)
    with col_next:
        # Find the max day that actually exists in this week from data
        days_in_current_week = [t['day'] for t in all_tasks if t['week'] == current_week]
        max_day_in_week = max(days_in_current_week) if days_in_current_week else 7

        if is_complete:
            # UNLOCKED: Bright, clickable, normal appearance
            if st.button("›", key=f"nav_next_{current_week}_{current_day}",
                        use_container_width=True, type="secondary"):
                if current_day < max_day_in_week:
                    return current_week, current_day + 1
                elif current_week < total_weeks:
                    return current_week + 1, 1  # First day of next week
        else:
            # LOCKED: Always visible but disabled
            st.button("🔒", 
                     key=f"nav_next_{current_week}_{current_day}_locked",
                     use_container_width=True, 
                     type="secondary",
                     disabled=True,
                     help="Complete today's tasks first!")
            
    
    # No navigation happened
    return current_week, current_day

def render_sidebar_recent_sessions(user_id):
    """Renders the 3 most recent sessions in the sidebar with colored score pills."""
    render_sidebar_header("Recent Missions", "🏆")


    sessions = storage.get_sessions(user_id) or []
    if not sessions:
        st.caption("No missions recorded yet. Start your first focus session!")
        return

    for s in sessions[:3]:
        try:
            dt       = datetime.fromisoformat(s['start_time'])
            time_str = dt.strftime("%b %d, %H:%M")
        except:
            time_str = "Recent"

        score = int(s.get('focus_score', 0))
        mins  = round(float(s.get('actual_duration', 0)), 1)
        phone   = s.get('phone_count', 0)
        drowsy  = s.get('drowsy_count', 0)
        zone    = s.get('zone_out_count', 0)

        if score >= 80:
            score_bg, score_color = "rgba(16,185,129,0.18)", "#10b981"
        elif score >= 60:
            score_bg, score_color = "rgba(245,158,11,0.18)", "#f59e0b"
        else:
            score_bg, score_color = "rgba(239,68,68,0.18)", "#ef4444"

        pills = []
        if phone:  pills.append(f"📱{phone}")
        if drowsy: pills.append(f"😴{drowsy}")
        if zone:   pills.append(f"👁{zone}")
        distraction_str = " · ".join(pills) if pills else "✅ Clean"


        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.18);
                    border-radius:12px; padding:10px 14px; margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.78rem; color:#94a3b8; font-weight:600;">{time_str}</span>
                <span style="font-size:0.75rem; font-weight:700; padding:2px 9px;
                             border-radius:20px; background:{score_bg}; color:{score_color};">{score}%</span>
            </div>
            <div style="display:flex; gap:10px; margin-top:5px; font-size:0.77rem; color:#cbd5e1;">
                <span>⏱ {mins}m</span>
                <span style="opacity:0.7;">{distraction_str}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("📊 View All Progress", key="side_view_progress", use_container_width=True):
        st.session_state.page = "Progress"
        st.rerun()