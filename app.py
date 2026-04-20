import streamlit as st
from utils import storage, ui_helper, email_helper
from modules import auth, profile_manager, roadmap, focus_tracker, doubt_solver, progress_analyzer, dashboard
import base64
import os
from datetime import datetime

# --- SCHEDULER SETUP ---
from apscheduler.schedulers.background import BackgroundScheduler

@st.cache_resource
def init_scheduler():
    scheduler = BackgroundScheduler()
    def check_reminders():
        profiles = storage.get_all_profiles()
        now = datetime.now()
        for p in profiles:
            uid = p.get("user_id")
            rem_time = p.get("reminder_time", "20:00")
            if not rem_time: continue
            try: rh, rm = map(int, rem_time.split(":"))
            except: continue
            
            # Use a slightly loose check depending on cron run (runs top of hour)
            if now.hour == rh:
                sessions = storage.get_sessions(uid)
                studied_today = False
                for s in sessions:
                    try:
                        s_time = datetime.strptime(s["start_time"], "%a %b %d %H:%M:%S %Y")
                        if s_time.date() == now.date():
                            studied_today = True; break
                    except: pass
                if not studied_today:
                    streak = storage.get_streak(uid)
                    email_helper.send_reminder_email(p.get("email"), p.get("name"), streak)

    scheduler.add_job(check_reminders, 'cron', minute=0)
    scheduler.start()
    return scheduler

_ = init_scheduler()

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

if "nav_to" in st.query_params:
    st.session_state.page = st.query_params["nav_to"]
    if "doubt_query" in st.query_params:
        st.session_state.doubt_query = st.query_params["doubt_query"]
    try:
        st.query_params.clear()
    except: pass

# Load profile
user_profile = None
if st.session_state.authenticated:
    user_profile = storage.get_profile(st.session_state.user_id)
    st.session_state.user_profile = user_profile

# Theme engine
current_theme = user_profile.get("theme", "Glass (Purple)") if user_profile else "Glass (Purple)"

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

    # Hex to RGB for transparency
    def hex_to_rgb(h): return ",".join([str(int(h.lstrip('#')[i:i+2], 16)) for i in (0, 2, 4)])
    p_rgb = hex_to_rgb(t['primary'])

    return f"""
    <div class="global-background"></div>
    <div class="global-bg-overlay"></div>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600;700&display=swap');
        :root {{ --primary: {t['primary']}; --primary-rgb: {p_rgb}; --secondary: {t['secondary']}; }}
        * {{ font-family: 'Inter', sans-serif; }}
        h1, h2, h3 {{ font-family: 'Outfit', sans-serif; font-weight: 800; color: white; }}
        
        /* 1. STABLE BACKGROUND SYSTEM */
        .stApp {{ background: transparent !important; }}
        .global-background {{
            position: fixed;
            top: -20px; left: -20px; 
            width: calc(100vw + 40px); height: calc(100vh + 40px);
            {bg_css}
            filter: blur(10px);
            -webkit-filter: blur(10px);
            z-index: -2;
            transform: scale(1.05);
            pointer-events: none;
            background-repeat: no-repeat;
            background-size: cover;
            background-color: #0d1117 !important; /* FALLBACK */
        }}
        .global-bg-overlay {{
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(13, 17, 23, 0.25) !important;
            z-index: -1;
            pointer-events: none;
        }}
        
        /* 2. FORCE TRANSPARENCY & LAYOUT FIXES */
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewBlockContainer"],
        [data-testid="stSidebar"],
        section[data-testid="stMain"],
        .stMain, .main, .block-container,
        [data-testid="stMainBlockContainer"],
        [data-testid="stVerticalBlock"],
        [data-testid="stDecoration"] {{
            background: transparent !important;
            background-color: transparent !important;
        }}

        /* 3. HARD SIDEBAR NAVIGATION HIDE */
        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}

        /* Components */
        .stCard {{
            background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px);
            border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);
            padding: 24px; margin-bottom: 20px;
        }}
        button[kind="primary"] {{
            background: linear-gradient(135deg, {t['primary']} 0%, {t['secondary']} 100%) !important;
            color: white !important; border: none !important;
        }}
        [data-testid="stMetricValue"] {{ font-size: 1.8rem !important; font-weight: 700 !important; }}

        /* Chat Bubbles */
        [data-testid="stChatMessage"] {{
            border-radius: 18px !important; padding: 12px 20px !important;
            margin-bottom: 12px !important;
            border: 1px solid rgba(255,255,255,0.08);
            width: fit-content !important; max-content: 85% !important;
        }}
        [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) {{
            background: linear-gradient(135deg, rgba(99,102,241,0.4) 0%, rgba(168,85,247,0.4) 100%) !important;
            margin-left: auto !important; border-bottom-right-radius: 4px !important;
        }}
        [data-testid="stChatMessage"]:has([aria-label="Chat message from assistant"]) {{
            background: rgba(30, 41, 59, 0.8) !important;
            margin-right: auto !important; border-bottom-left-radius: 4px !important;
        }}
    </style>
    """

st.markdown(get_theme_css(current_theme, st.session_state.get("authenticated", False)), unsafe_allow_html=True)

# --- AUTH GATE ---
if not st.session_state.authenticated:
    ui_helper.apply_navbar_fix("Login", [])
    auth.main()
else:
    # Navigation Structure
    if not user_profile:
        pages = ["Setup Profile"]
        if st.session_state.page not in pages:
            st.session_state.page = "Setup Profile"
    else:
        pages = ["Dashboard", "Roadmap", "Focus Timer", "Doubt Solver", "Progress", "Settings"]
        if st.session_state.page not in pages:
            st.session_state.page = "Dashboard"

    if "navigate_to" in st.session_state:
        st.session_state.nav_radio = st.session_state.navigate_to
        st.session_state.page = st.session_state.navigate_to
        del st.session_state.navigate_to

    # --- GLOBAL UI LOCKDOWN & TOP NAVBAR ---
    # DEBUG: Force sidebar engine check
    st.sidebar.error("🚨 SIDEBAR ENGINE ACTIVE (NESTED)")
    ui_helper.apply_navbar_fix(st.session_state.page, pages)

    # Hidden radio — JS in fixed navbar clicks the matching label to trigger rerun
    st.markdown('<div id="hide-this-nav-radio" style="display: none;"></div>', unsafe_allow_html=True)
    page = st.radio("", pages, horizontal=True,
                    index=pages.index(st.session_state.page),
                    label_visibility="collapsed", key="nav_radio")
    if page != st.session_state.page:
        st.session_state.page = page
        st.rerun()


    # --- ROUTING LOGIC ---
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