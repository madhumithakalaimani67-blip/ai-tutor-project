import streamlit as st
import streamlit.components.v1 as components

def apply_navbar_fix(active_page, pages):
    show_sidebar_pages = ["Roadmap", "Focus Timer", "Doubt Solver"]

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
    /* Hide default Streamlit toolbars and the sidebar's default page nav */
    #MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }

    /* Make the Streamlit header transparent. We use pointer-events: none on the header
       and pointer-events: auto on its children so that the hamburger button is clickable
       but clicks pass through the rest of the header to our custom navbar. */
    [data-testid="stHeader"] {
        background: transparent !important;
        z-index: 10000 !important;
        pointer-events: none !important;
        height: 70px !important;
    }
    
    [data-testid="stHeader"] * {
        pointer-events: auto !important;
    }

    /* Permanently hide the entire sidebar header (which contains the << button) 
       to prevent the user from accidentally closing it. */
    [data-testid="stSidebar"] [data-testid="stSidebarHeader"],
    [data-testid="stSidebar"] button[kind="header"],
    button[aria-label="Close sidebar"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    /* Position the re-open button (>>) BELOW the navbar so it's never buried.
       We place it at top: 85px (70px navbar + 15px margin). */
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
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 42px !important;
        height: 42px !important;
        visibility: visible !important;
        color: white !important;
    }

    #eduai-nav-block {
        position: fixed !important;
        top: 0 !important; left: 0 !important; right: 0 !important;
        height: 70px !important; z-index: 9999 !important;
        background: #0d1117 !important;
        border-bottom: 2px solid rgba(255,255,255,0.1) !important;
        padding: 0 40px 0 60px !important; margin: 0 !important;
        display: flex !important; align-items: center !important;
    }
    
    [data-testid="stAppViewBlockContainer"] { padding-top: 85px !important; }
    
    /* Position the native sidebar beneath the top navbar */
    section[data-testid="stSidebar"] {
        top: 70px !important;
        height: calc(100vh - 70px) !important;
        background: rgba(13,17,23,0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
    }

    /* Hide the native sidebar collapse button inside the sidebar since we'll use branding there */
    [data-testid="stSidebar"] button[kind="header"] {
        display: none !important;
    }

    .eduai-logo {
        font-size: 1.15rem !important; font-weight: 800 !important;
        background: linear-gradient(135deg,#6366f1,#a855f7) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        white-space: nowrap !important; margin-right: auto !important;
        display: block !important;
    }
    #eduai-nav-block [data-testid="stColumn"]:not(:first-child) button {
        background: transparent !important; border: none !important;
        border-bottom: 2px solid transparent !important;
        color: #9ca3af !important; font-size: 13.5px !important;
        cursor: pointer !important; padding: 8px 4px !important;
        font-weight: 400 !important; box-shadow: none !important;
        border-radius: 0 !important; white-space: nowrap !important;
        width: auto !important; min-width: 0 !important;
    }
    #eduai-nav-block [data-testid="stColumn"]:not(:first-child) [data-testid="stBaseButton-primary"] {
        color: #ffffff !important;
        border-bottom: 2px solid #6366f1 !important;
        font-weight: 600 !important;
    }
    #eduai-nav-block [data-testid="stColumn"]:not(:first-child) button:hover {
        color: #ffffff !important; background: transparent !important;
    }

    /* Sidebar panel (built via columns, acts like native sidebar) */
    .eduai-sidebar-panel {
        background: rgba(13,17,23,0.92) !important;
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        padding: 20px 16px !important;
        height: calc(100vh - 105px) !important;
        position: sticky !important;
        top: 85px !important;
        overflow-y: auto !important;
    }
    .sidebar-header {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important; font-size: 1.3rem !important;
        background: linear-gradient(135deg,#6366f1,#a855f7);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        margin-bottom: 4px !important; letter-spacing: -0.5px !important;
    }
    .sidebar-divider {
        height: 1px;
        background: linear-gradient(90deg,rgba(99,102,241,0.5),transparent);
        margin: 6px 0 16px 0;
    }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.4); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

    components.html("""
    <script>
    (function() {
        function tagNavBlock() {
            var pdoc = window.parent.document;
            var blocks = pdoc.querySelectorAll('[data-testid="stHorizontalBlock"]');
            if (blocks.length > 0) {
                blocks[0].id = 'eduai-nav-block';
            } else {
                setTimeout(tagNavBlock, 100);
            }
        }
        tagNavBlock();

        function autoExpandSidebar() {
            var pdoc = window.parent.document;
            
            // 1. Surgical strike on localStorage to reset the 'stuck' state in browsers like Edge
            try {
                var keys = Object.keys(window.parent.localStorage);
                for (var i = 0; i < keys.length; i++) {
                    if (keys[i].includes('stSidebarCollapsed')) {
                        window.parent.localStorage.setItem(keys[i], 'false');
                    }
                }
            } catch (e) {}

            // 2. Aggressive button finder
            var btn = pdoc.querySelector('button[aria-label="Open sidebar"]') || 
                      pdoc.querySelector('[data-testid="collapsedControl"]') ||
                      pdoc.querySelector('[data-testid="stSidebarCollapsedControl"]') ||
                      pdoc.querySelector('section[data-testid="stHeader"] button');
            
            if (btn && btn.offsetParent !== null) { // If button exists and is visible
                btn.click();
            }
        }
        
        // Multiple triggers to catch it at any point during browser load
        setTimeout(autoExpandSidebar, 300);
        setTimeout(autoExpandSidebar, 1000);
        setTimeout(autoExpandSidebar, 3000);
    })();
    </script>
    """, height=0, scrolling=False)


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
    """Render the premium EDUAI logo and title at the top of the sidebar."""
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
    <div class="sidebar-header">{icon} {title}</div>
    <div class="sidebar-divider"></div>
    """, unsafe_allow_html=True)


def begin_sidebar_layout():
    """Call this at the top of sidebar-page modules.
    Returns (sidebar_col, main_col). Renders the toggle button."""
    # Toggle state
    if "sidebar_open" not in st.session_state:
        st.session_state.sidebar_open = True

    if st.session_state.sidebar_open:
        cols = st.columns([1.1, 3.9])
    else:
        cols = st.columns([0.12, 4.88])

    return cols[0], cols[1]


def render_sidebar_toggle():
    """Render the << >> collapse toggle button."""
    is_open = st.session_state.get("sidebar_open", True)
    icon = "<<" if is_open else ">>"
    tooltip = "Collapse sidebar" if is_open else "Expand sidebar"
    if st.button(icon, key="sidebar_toggle_btn", help=tooltip):
        st.session_state.sidebar_open = not st.session_state.sidebar_open
        st.rerun()


def apply_active_highlight(idx):
    pass