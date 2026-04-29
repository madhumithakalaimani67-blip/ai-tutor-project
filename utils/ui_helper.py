import streamlit as st
import streamlit.components.v1 as components
import json

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

    /* 5. Jump to Bottom Button (Gemini/ChatGPT Style) */
    #jump-to-bottom-btn {
        position: fixed;
        bottom: 120px;
        left: 50%;
        transform: translateX(-50%) translateY(15px) scale(0.9);
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #f8fafc !important;
        width: 38px !important;
        height: 38px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        z-index: 1000000 !important;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    }
    #jump-to-bottom-btn.visible {
        opacity: 1 !important;
        visibility: visible !important;
        transform: translateX(-50%) translateY(0) scale(1) !important;
    }
    #jump-to-bottom-btn:hover {
        background: rgba(45, 55, 72, 0.9) !important;
        color: #ffffff !important;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5) !important;
    }
    #jump-to-bottom-btn:active {
        transform: translateX(-50%) scale(0.95) !important;
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

def render_jump_to_bottom():
    """Renders the jump-to-bottom floating button div and JS logic."""
    st.markdown("""
        <div id="jump-to-bottom-btn" title="Jump to recent messages">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
        </div>
    """, unsafe_allow_html=True)
    
    components.html("""
    <script>
    (function() {
        var pdoc = window.parent.document;
        var mainContainer = pdoc.querySelector('.main') || pdoc.querySelector('[data-testid="stAppViewMain"]');
        var btn = pdoc.getElementById('jump-to-bottom-btn');
        
        if (!mainContainer || !btn) return;

        function handleScroll() {
            var threshold = 400;
            var fromBottom = mainContainer.scrollHeight - mainContainer.scrollTop - mainContainer.clientHeight;
            if (mainContainer.scrollTop > threshold && fromBottom > 150) {
                btn.classList.add('visible');
            } else {
                btn.classList.remove('visible');
            }
        }

        mainContainer.addEventListener('scroll', handleScroll);
        btn.onclick = function() {
            mainContainer.scrollTo({ top: mainContainer.scrollHeight, behavior: 'smooth' });
        };
        handleScroll();
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
        <div style="font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 1.6rem; 
                    background: linear-gradient(135deg, #6366f1, #a855f7);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    margin-bottom: 0;">
            EDUAI 🧠
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
    Parses AI markdown roadmap and renders it as a premium visual pathway.
    Enhanced to be more robust and clean.
    """
    if not content: return
    
    import re
    
    # 1. First, check if this looks like a roadmap at all.
    # If it contains both "Week" and "Day", we try to parse it.
    if not (re.search(r'Week\s*\d+', content, re.I) and re.search(r'Day\s*\d+', content, re.I)):
        st.markdown(content)
        return
    
    weeks = []
    current_week = None
    current_day = None
    
    lines = content.split('\n')
    for line in lines:
        raw_line = line.strip()
        if not raw_line: continue
        
        # Clean line for detection
        clean_line = re.sub(r'^[\s\*\-\+\#\>\d\.]+', '', raw_line).strip()
        
        # Detect Week (e.g., Week 1, **Week 1**, ### Week 1)
        if re.match(r'Week\s*\d+', clean_line, re.I) or (re.search(r'Week\s*\d+', raw_line, re.I) and (raw_line.startswith('**') or raw_line.startswith('###'))):
            # Extract just the title part
            title = clean_line if clean_line else raw_line.replace('*','').replace('#','').strip()
            current_week = {"title": title, "days": []}
            weeks.append(current_week)
            current_day = None
            continue
        
        # Detect Day (e.g., Day 1, **Day 1**, + Day 1)
        if re.match(r'Day\s*\d+', clean_line, re.I) and current_week is not None:
            title = clean_line
            current_day = {"title": title, "tasks": []}
            current_week["days"].append(current_day)
            continue
            
        # Detect Task (anything else if we are inside a day)
        if current_day is not None:
            task_text = clean_line
            if task_text and not re.match(r'Week\s*\d+', task_text, re.I) and not re.match(r'Day\s*\d+', task_text, re.I):
                current_day["tasks"].append(task_text)

    # Final check: if we found no weeks, fallback
    if not weeks:
        st.markdown(content)
        return

    # 2. Render HTML
    html = '<div class="roadmap-container"><div class="roadmap-pathway"></div>'
    
    for week in weeks:
        # Clean the week title from trailing bold markers
        w_title = week["title"].replace('**', '').strip()
        html += '<div class="roadmap-week-section">'
        html += '<div class="roadmap-week-node">'
        html += '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
        html += '<polyline points="20 6 9 17 4 12"></polyline></svg></div>'
        html += '<div class="roadmap-card">'
        html += f'<div class="roadmap-week-title">{w_title}</div>'
        
        for day in week["days"]:
            # Clean day title
            d_title = day["title"].replace('**', '').strip()
            html += '<div class="roadmap-day-item">'
            html += '<div class="roadmap-day-title">'
            html += f'<span style="color:#a855f7;">◈</span> {d_title}</div>'
            html += '<div class="roadmap-tasks">'
            for task in day["tasks"]:
                clean_task = task.replace('**', '').strip()
                html += f'<div class="roadmap-task-pill">{clean_task}</div>'
            html += '</div></div>'
            
        html += '</div></div>'
    
    html += '</div>'
    
    # Wrap in a single markdown call to ensure it's treated as one block
    st.markdown(html, unsafe_allow_html=True)

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