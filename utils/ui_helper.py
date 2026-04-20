import streamlit as st
import streamlit.components.v1 as components

def apply_navbar_fix(active_page, pages):
    show_sidebar_pages = ["Roadmap", "Focus Timer", "Doubt Solver"]

    # ── LOGIN PAGE: only hide native chrome, no navbar ──
    if not pages:
        st.markdown("""
        <style>
        <style>
        #MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stSidebarNav"] { display: none !important; }
        [data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        </style>
        """, unsafe_allow_html=True)
        return
    if active_page in show_sidebar_pages:
        hide_sidebar_css = ""
    else:
        # TEMP: Disabled hiding for debugging
        hide_sidebar_css = "" 
        # hide_sidebar_css = """
        # section[data-testid="stSidebar"] {
        #     display: none !important;
        # }
        # """

    # Build nav items — Pure HTML spans with data-index tags (NO inline JS for Streamlit to strip)
    nav_items_html = ""
    for idx, page in enumerate(pages):
        if page == active_page:
            style = ("color:#ffffff; border-bottom:2px solid #6366f1;"
                     " font-weight:600; padding-bottom:2px;")
        else:
            style = "color:#9ca3af;"
        
        nav_items_html += (
            f'<span class="eduai-nav-item" style="{style}" '
            f'data-index="{idx}">{page}</span>'
        )

    st.markdown(f"""
    <!-- EDUAI FIXED NAVBAR -->
    <div class="eduai-navbar" id="eduai-custom-navbar">
        <span class="eduai-logo">EDUAI&nbsp;|</span>
        <div class="eduai-nav-links">
            {nav_items_html}
        </div>
    </div>

    <style>
    /* ── 1. FIXED TOP NAVBAR ── */
    .eduai-navbar {{
        position: fixed;
        top: 0; left: 60px; right: 0;
        z-index: 1000001;
        height: 56px;
        background: #0d1117;
        border-bottom: 1px solid #1f2937;
        border-top-left-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: flex-end; /* Aligns EVERYTHING to the right */
        padding: 0 40px;
        gap: 32px; /* Space between logo and links */
        box-sizing: border-box;
    }}
    .eduai-nav-links {{
        display: flex;
        align-items: center;
        gap: 32px;
    }}
    .eduai-logo {{
        font-size: 1.15rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        white-space: nowrap;
        flex-shrink: 0;
    }}
    .eduai-nav-item {{
        font-size: 13.5px;
        text-decoration: none !important;
        cursor: pointer;
        transition: color 0.2s ease;
        white-space: nowrap;
    }}
    .eduai-nav-item:hover {{ color: #ffffff !important; }}

    /* ── 2. HIDE ONLY THE NAVBAR STREAMLIT RADIO (keep it in DOM for JS to click) ── */
    div[data-testid="stRadio"]:first-of-type {{
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        opacity: 0 !important;
        position: absolute !important;
        top: -9999px !important;
    }}

    /* ── 3. PUSH CONTENT BELOW FIXED BAR ── */
    [data-testid="stAppViewBlockContainer"] {{
        padding-top: 76px !important;
    }}

    /* ── 4. HIDE STREAMLIT NATIVE CHROME ── */
    #MainMenu, footer, [data-testid="stToolbar"] {{
        display: none !important;
    }}
    [data-testid="stHeader"] {{
        background: transparent !important;
        z-index: 1000002 !important; /* Above our custom navbar */
        box-shadow: none !important;
        pointer-events: none; /* Let clicks pass through... */
    }}
    [data-testid="stHeader"] * {{ pointer-events: auto; /* ...except for the hamburger icon */ }}

    /* Ensure toggle button is clickable */
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] {{
        z-index: 1000003 !important;
    }}

    /* ── 5. CONDITIONAL SIDEBAR ── */
    [data-testid="stSidebarNav"] {{ display: none !important; }}
    
    {hide_sidebar_css}

    /* Glassmorphism for the sidebar (REFINED) */
    section[data-testid="stSidebar"], 
    [data-testid="stSidebar"],
    section[aria-label="Sidebar"],
    .stSidebar {{
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 5px solid #ef4444 !important; /* AGGRESSIVE DEBUG RED BORDER */
        visibility: visible !important;
        opacity: 1 !important;
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    import time
    
    # Safely inject JS completely side-stepping DOMPurify using a 0px iframe!
    # By injecting a dynamic timestamp, we forcefully banish Streamlit's iframe cache.
    # The javascript Engine executes completely fresh and surgically binds directly to the current page's DOM.
    js_code = f"""
    <script>
    (function() {{
        const parentDoc = window.parent.document;
        const navItems = parentDoc.querySelectorAll('.eduai-nav-item');
        
        navItems.forEach(item => {{
            item.onclick = function() {{
                const targetPageText = this.textContent.trim();
                const radioGroup = parentDoc.querySelector('[data-testid="stRadio"]');
                if (radioGroup) {{
                    const walker = parentDoc.createTreeWalker(radioGroup, NodeFilter.SHOW_TEXT, null, false);
                    let node;
                    while (node = walker.nextNode()) {{
                        if (node.nodeValue.trim() === targetPageText) {{
                            const parent = node.parentElement;
                            const clickable = parent.closest('label') || parent.closest('[role="radio"]') || parent;
                            clickable.click();
                            break;
                        }}
                    }}
                }}
            }};
        }});
    }})();
    </script>
    """
    components.html(js_code, height=0, width=0)

def apply_active_highlight(idx):
    pass
