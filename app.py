import streamlit as st
from utils import storage
from modules import auth, profile_manager, roadmap, focus_tracker, doubt_solver, progress_analyzer, dashboard

# Page config
st.set_page_config(
    page_title="EDUAI - AI Study Companion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# Load profile
user_profile = None
if st.session_state.authenticated:
    user_profile = storage.get_profile(st.session_state.user_id)
    st.session_state.user_profile = user_profile

# Theme engine
current_theme = user_profile.get("theme", "Glass (Purple)") if user_profile else "Glass (Purple)"

import base64
import os

def get_base64_bg(is_auth=False):
    filename = "app_background.png" if is_auth else "eduai_background.png"
    bg_path = os.path.join("assets", filename)
    if os.path.exists(bg_path):
        with open(bg_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return ""

def get_theme_css(theme_name, is_auth=False):
    themes = {
        "Glass (Purple)": {
            "primary": "#6366f1", "secondary": "#a855f7", "bg": "#0f172a"
        },
        "Ocean Blue": {
            "primary": "#0ea5e9", "secondary": "#2dd4bf", "bg": "#082f49"
        },
        "Midnight Gold": {
            "primary": "#fbbf24", "secondary": "#d97706", "bg": "#111827"
        }
    }
    t = themes.get(theme_name, themes["Glass (Purple)"])
    bg_b64 = get_base64_bg(is_auth)
    
    if bg_b64:
        bg_css = f'background-image: url("data:image/png;base64,{bg_b64}"); background-size: cover; background-position: center; background-attachment: fixed;'
    else:
        bg_css = f'background-color: {t["bg"]};'

    nav_css = """
        /* TAB-LIKE HORIZONTAL NAVIGATION OVERRIDE - ONLY FOR THE TOP-LEVEL NAV BAR */
        [data-testid="stAppViewBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(2) [data-testid="stHorizontalBlock"] {
            border-bottom: 2px solid rgba(255,255,255,0.12);
            margin-bottom: 30px;
            position: sticky;
            top: 0;
            z-index: 999;
            background: rgba(15, 23, 42, 0.98) !important;
            backdrop-filter: blur(25px) !important;
            padding-top: 18px;
            padding-bottom: 8px;
        }
        [data-testid="stAppViewBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(2) [data-testid="stHorizontalBlock"] .stButton>button {
            background: transparent !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 8px 0 !important;
            color: rgba(255,255,255,0.6) !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        [data-testid="stAppViewBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(2) [data-testid="stHorizontalBlock"] .stButton>button:hover {
            color: white !important;
            background: rgba(255,255,255,0.08) !important;
        }
    """ if is_auth else ""

    # Hex to RGB for transparency
    def hex_to_rgb(h): return ",".join([str(int(h.lstrip('#')[i:i+2], 16)) for i in (0, 2, 4)])
    p_rgb = hex_to_rgb(t['primary'])

    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600;700&display=swap');
        :root {{ --primary: {t['primary']}; --primary-rgb: {p_rgb}; --secondary: {t['secondary']}; }}
        * {{ font-family: 'Inter', "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif; }}
        h1, h2, h3 {{
            font-family: 'Outfit', sans-serif; font-weight: 800;
            color: white;
        }}
        .stApp {{ {bg_css} }}
        /* ── NUKE ALL UNWANTED OUTER/INNER BOXES (AGRESSIVE) ── */
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewBlockContainer"],
        section[data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stVerticalBlock"],
        .main, .main .block-container,
        .block-container,
        .stApp > div,
        .stApp > section,
        [data-testid="stDecoration"],
        [data-testid="stHeader"] {{
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            border: none !important;
        }}
        {nav_css}
        .global-bg-overlay {{
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: {t['bg']}88;
            backdrop-filter: blur(12px);
            z-index: 0;
            pointer-events: none;
        }}
        [data-testid="stSidebar"] {{
            background-color: rgba(15, 23, 42, 0.5) !important;
            backdrop-filter: blur(25px); border-right: 1px solid rgba(255,255,255,0.1);
        }}
        .stCard {{
            background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px);
            border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);
            padding: 24px; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}

        /* DEFAULT SUBTLE BUTTONS (Dashboard Cards) */
        .stButton>button {{
            background: rgba(255,255,255,0.03) !important;
            color: rgba(255,255,255,0.85) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            font-weight: 600 !important; border-radius: 12px !important;
            padding: 8px 16px !important; transition: all 0.2s ease !important;
        }}
        .stButton>button:hover {{
            color: white !important; background: rgba(255,255,255,0.1) !important;
        }}

        /* GLOBAL PRIMARY BUTTONS */
        button[kind="primary"], [data-testid="stFormSubmitButton"] > button {{
            background: linear-gradient(135deg, {t['primary']} 0%, {t['secondary']} 100%) !important;
            color: white !important; border: none !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        }}
        button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] > button:hover {{
            transform: translateY(-2px); box-shadow: 0 10px 20px -10px {t['primary']} !important;
        }}
        [data-testid="stMetricValue"] {{ font-size: 1.8rem !important; font-weight: 700 !important; }}

        /* --- CHAT BUBBLE ALIGNMENT --- */
        [data-testid="stChatMessage"] {{ 
            border-radius: 18px !important; 
            padding: 12px 20px !important; 
            margin-bottom: 12px !important; 
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            line-height: 1.5 !important;
            width: fit-content !important; /* Premium fit-content bubbles */
            max-width: 85% !important;
        }}
        /* USER: RIGHT */
        [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) {{
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.4) 0%, rgba(168, 85, 247, 0.4) 100%) !important;
            margin-left: auto !important; /* Push to right */
            border-bottom-right-radius: 4px !important;
        }}
        /* ASSISTANT: LEFT */
        [data-testid="stChatMessage"]:has([aria-label="Chat message from assistant"]) {{
            background: rgba(30, 41, 59, 0.8) !important;
            margin-right: auto !important; /* Push to left */
            border-bottom-left-radius: 4px !important;
        }}
        [data-testid="stChatMessageContent"] {{ overflow-wrap: break-word !important; }}

        /* --- STICKY NAV REFINEMENT --- */
        [data-testid="stHeader"] {{ background: transparent !important; }} /* Restore for toggle */
        [data-testid="stDeployButton"] {{ display: none !important; }} /* Hide Deploy */
        footer {{ display: none !important; }} 
    </style>
    <div class="global-bg-overlay"></div>
    """

st.markdown(get_theme_css(current_theme, st.session_state.get("authenticated", False)), unsafe_allow_html=True)

# --- AUTH GATE ---
if not st.session_state.authenticated:
    auth.main()
else:
    # Navigation Structure
    if not user_profile:
        pages = ["Setup Profile"]
    else:
        pages = ["Dashboard", "Roadmap", "Focus Timer", "Doubt Solver", "Progress", "Settings"]

    icons = {
        "Setup Profile": "Setup Profile", "Dashboard": "Dashboard", "Roadmap": "Roadmap", "Focus Timer": "Focus Timer",
        "Doubt Solver": "Doubt Solver", "Progress": "Progress", "Settings": "Settings"
    }

    # --- TOP HORIZONTAL NAVIGATION (Upper Window) ---
    nav_cols = st.columns([1.5] + [1.4] * len(pages))
    
    with nav_cols[0]:
        st.markdown(f"<h3 style='margin:0; padding-top: 5px; color: var(--primary); letter-spacing: 1px;'>EDUAI</h3>", unsafe_allow_html=True)
        
    for idx, p in enumerate(pages):
        with nav_cols[idx+1]:
            # Tab highlight logic (Active Tab state)
            if st.session_state.page == p:
                st.markdown(f"""
                    <style>
                        div[data-testid='column']:nth-child({idx+2}) button {{
                            color: white !important;
                            background: var(--primary) !important;
                            box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
                        }}
                    </style>
                """, unsafe_allow_html=True)
            
            if st.button(p, key=f"nav_{p}", use_container_width=True):
                st.session_state.page = p
                st.rerun()
                
    # Inactivity Alert (Global instead of sidebar)
    if user_profile:
        from datetime import datetime, timedelta
        sessions = storage.get_sessions(st.session_state.user_id)
        if sessions:
            last_s = sessions[0]
            try:
                last_dt = datetime.strptime(last_s['end_time'], "%a %b %d %H:%M:%S %Y")
                if datetime.now() - last_dt > timedelta(hours=24):
                    st.warning("🌙 You've been away for a while! Ready to jump back in?")
            except: pass

    # --- ROUTING ---
    page = st.session_state.page

    if not user_profile:
        profile_manager.main(st.session_state.user_id)
    elif page == "Dashboard":
        dashboard.main(st.session_state.user_id, user_profile)
    elif page == "Roadmap":
        roadmap.main(st.session_state.user_id)
    elif page == "Focus Timer":
        focus_tracker.main(st.session_state.user_id)
    elif page == "Doubt Solver":
        doubt_solver.main()
    elif page == "Progress":
        progress_analyzer.main(st.session_state.user_id)
    elif page == "Settings":
        st.title("⚙️ Settings")
        
        st.markdown("### 🎨 Theme")
        new_theme = st.selectbox("Select Theme", ["Glass (Purple)", "Ocean Blue", "Midnight Gold"],
            index=["Glass (Purple)", "Ocean Blue", "Midnight Gold"].index(current_theme))
        if new_theme != current_theme:
            storage.update_theme(st.session_state.user_id, new_theme)
            st.success(f"Theme changed to {new_theme}!")
            st.rerun()

        st.markdown("---")
        st.markdown("### 🗑 Account")
        if st.button("Reset Profile & Start Over"):
            storage.full_reset(st.session_state.user_id)
            st.session_state.user_profile = None
            st.session_state.page = "Setup Profile"
            st.rerun()
            
        st.markdown("---")
        st.markdown("### 🚪 Application")
        if st.button("Logout of EDUAI", type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; opacity: 0.4; font-size: 0.85rem;'>Made with ❤️ by EduNeurons</p>", unsafe_allow_html=True)