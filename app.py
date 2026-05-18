import streamlit as st

from utils import storage, ui_helper, email_helper
from modules import auth, profile_manager, roadmap, focus_tracker, doubt_solver, progress_analyzer, dashboard
import base64
import os
import json
from datetime import datetime

st.set_page_config(
    page_title="EDUAI - AI Study Companion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
            if now.hour == rh:
                sessions = storage.get_sessions(uid)
                studied_today = False
                for s in sessions:
                    try:
                        s_time = datetime.strptime(s["start_time"], "%Y-%m-%d %H:%M:%S")
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

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

user_profile = None
if st.session_state.authenticated:
    user_profile = storage.get_profile(st.session_state.user_id)
    st.session_state.user_profile = user_profile

    # Inject user_id into localStorage for the JS Focus Tracker
    import streamlit.components.v1 as components
    components.html(f"""
    <script>
    try {{ window.top.localStorage.setItem('eduai_user_id', '{st.session_state.user_id}'); }} catch(e) {{}}
    </script>
    """, height=0)

    

    # ── Background Focus Persistence ──
    if 'eye_state' not in st.session_state:
        st.session_state.eye_state = {"running": False, "start_time": 0, "score": 100, "counts": {"phone":0,"drowsy":0,"zone_out":0}}

    # Handle background focus sync & global saving
    # Resolve duration for global persistence
    current_rm_id = st.session_state.get("current_roadmap_id")
    active_roadmap = storage.get_roadmap_by_id(st.session_state.user_id, current_rm_id) if current_rm_id else storage.get_latest_roadmap(st.session_state.user_id)
    today_task = None
    if active_roadmap:
        tasks = storage.get_tasks(st.session_state.user_id, active_roadmap['id'])
        pending = [t for t in tasks if t['status'] == 'pending']
        if pending: today_task = pending[0]
        
    duration, _ = focus_tracker.get_session_duration(today_task, user_profile)
    ui_helper.render_focus_sync_background(st.session_state.user_id, duration)
    
    # Background focus tracker embed removed - using URL query params instead

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
        "Glass (Purple)": {"primary": "#6366f1", "secondary": "#a855f7", "bg": "#0f172a"},
        "Ocean Blue":     {"primary": "#0ea5e9", "secondary": "#2dd4bf", "bg": "#082f49"},
        "Midnight Gold":  {"primary": "#fbbf24", "secondary": "#d97706", "bg": "#111827"},
    }
    t = themes.get(theme_name, themes["Glass (Purple)"])
    bg_b64 = get_base64_bg(is_auth)

    if bg_b64:
        bg_css = f'background-image: url("data:image/png;base64,{bg_b64}"); background-size: cover; background-position: center; background-attachment: fixed;'
    else:
        bg_css = f'background-color: {t["bg"]};'

    def hex_to_rgb(h): return ",".join([str(int(h.lstrip('#')[i:i+2], 16)) for i in (0, 2, 4)])
    p_rgb = hex_to_rgb(t['primary'])

    return f"""
    <div class="global-background"></div>
    <div class="global-bg-overlay"></div>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600;700&display=swap');
        :root {{ --primary: {t['primary']}; --primary-rgb: {p_rgb}; --secondary: {t['secondary']}; }}
        * {{ margin:0; padding:0; box-sizing:border-box; font-family:'Inter',sans-serif; -webkit-font-smoothing:antialiased; }}
        html, body, [data-testid="stApp"] {{ background-color: transparent !important; }}
        h1, h2, h3 {{ font-family:'Outfit',sans-serif; font-weight:800; color:white; }}
        .stApp {{ background: transparent !important; }}
        .global-background {{
            position:fixed; top:-20px; left:-20px;
            width:calc(100vw + 40px); height:calc(100vh + 40px);
            {bg_css}
            filter:blur(10px); -webkit-filter:blur(10px);
            z-index:-2; transform:scale(1.05) translateZ(0);
            pointer-events:none; background-repeat:no-repeat;
            background-size:cover; background-color:#0d1117 !important;
            will-change:transform,filter;
        }}
        .global-bg-overlay {{
            position:fixed; top:0; left:0; width:100vw; height:100vh;
            background:rgba(13,17,23,0.25) !important;
            z-index:-1; pointer-events:none;
        }}
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewBlockContainer"],
        section[data-testid="stMain"],
        .stMain, .main, .block-container,
        [data-testid="stMainBlockContainer"],
        [data-testid="stVerticalBlock"],
        [data-testid="stDecoration"] {{ background:transparent !important; background-color:transparent !important; }}
        [data-testid="stSidebarNav"] {{ display:none !important; }}
        .stCard {{
            background:rgba(30,41,59,0.7); backdrop-filter:blur(10px);
            -webkit-backdrop-filter:blur(10px); border-radius:20px;
            border:1px solid rgba(255,255,255,0.1); padding:24px; margin-bottom:20px;
        }}
        button[kind="primary"] {{
            background:linear-gradient(135deg,{t['primary']} 0%,{t['secondary']} 100%) !important;
            color:white !important; border:none !important;
        }}
        [data-testid="stMetricValue"] {{ font-size:1.8rem !important; font-weight:700 !important; }}
        [data-testid="stChatMessage"] {{
            border-radius:18px !important; padding:12px 20px !important;
            margin-bottom:12px !important; border:1px solid rgba(255,255,255,0.08);
            width:fit-content !important;
        }}
        [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) {{
            background:linear-gradient(135deg,rgba(99,102,241,0.4) 0%,rgba(168,85,247,0.4) 100%) !important;
            margin-left:auto !important; border-bottom-right-radius:4px !important;
        }}
        [data-testid="stChatMessage"]:has([aria-label="Chat message from assistant"]) {{
            background:rgba(30,41,59,0.8) !important;
            margin-right:auto !important; border-bottom-left-radius:4px !important;
        }}
    </style>
    """

st.markdown(get_theme_css(current_theme, st.session_state.get("authenticated", False)), unsafe_allow_html=True)

if not st.session_state.authenticated:
    ui_helper.apply_navbar_fix("Login", [])
    auth.main()
else:
    if not user_profile:
        pages = ["Setup Profile"]
        if st.session_state.page not in pages:
            st.session_state.page = "Setup Profile"
    else:
        pages = ["Dashboard", "Roadmap", "Focus Timer", "Doubt Solver", "Progress", "Settings"]
        if st.session_state.page not in pages:
            st.session_state.page = "Dashboard"
            
        # Global roadmap context initialization
        if "current_roadmap_id" not in st.session_state:
            all_rms = storage.get_all_roadmaps(st.session_state.user_id)
            if all_rms:
                st.session_state.current_roadmap_id = all_rms[0]['id']
            else:
                st.session_state.current_roadmap_id = None


    if "navigate_to" in st.session_state:
        target = st.session_state.navigate_to
        del st.session_state.navigate_to
        st.session_state.page = target
        if "nav_radio" in st.session_state:
            del st.session_state["nav_radio"]
        st.rerun()


    # Apply CSS layout
    ui_helper.apply_navbar_fix(st.session_state.page, pages)

    # Render nav buttons — MUST be first st.columns() call so JS can tag them
    ui_helper.render_nav_buttons(st.session_state.page, pages)

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
        
        profile_manager.main(st.session_state.user_id, existing_profile=st.session_state.user_profile, is_setup=False)
        st.markdown("---")
        
        st.markdown("### 🔥 Activity & Streak")
        history = storage.get_login_history(st.session_state.user_id)
        streak = storage.get_streak(st.session_state.user_id)
        
        from datetime import datetime, timedelta
        today = datetime.now().date()
        
        if "heatmap_year" not in st.session_state:
            st.session_state.heatmap_year = today.year
            
        target_year = st.session_state.heatmap_year
        
        # Navigation
        nav_col1, nav_col2, nav_col3, _ = st.columns([0.5, 2, 0.5, 7])
        with nav_col1:
            if st.button("◀", key="prev_year"):
                st.session_state.heatmap_year -= 1
                st.rerun()
        with nav_col2:
            st.markdown(f"<h4 style='text-align:center; margin-top:5px;'>{target_year}</h4>", unsafe_allow_html=True)
        with nav_col3:
            if st.button("▶", key="next_year"):
                st.session_state.heatmap_year += 1
                st.rerun()

        # Start at the first Sunday on or before Jan 1
        jan1 = datetime(target_year, 1, 1).date()
        days_to_sunday = (jan1.weekday() + 1) % 7
        start_date = jan1 - timedelta(days=days_to_sunday)
        
        # End at Dec 31
        end_date = datetime(target_year, 12, 31).date()
        
        login_dates = set(history)
        
        month_labels_html = '<div style="display: flex; gap: 4px; height: 20px; margin-left: 29px;">'
        curr_m = start_date
        current_month = -1
        while curr_m <= end_date:
            if curr_m.month != current_month:
                current_month = curr_m.month
                month_name = curr_m.strftime("%b")
                month_labels_html += f'<div style="font-size: 0.7rem; opacity: 0.7; width: 14px; overflow: visible; white-space: nowrap;">{month_name}</div>'
            else:
                month_labels_html += '<div style="width: 14px;"></div>'
            curr_m += timedelta(days=7)
        month_labels_html += '</div>'
        
        html = f"""
        <div style="background: rgba(30,41,59,0.7); padding: 20px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; overflow-x: auto;">
            <h3 style="margin-top:0; display:flex; align-items:center; gap:10px;">
                Current Streak: <span style="color:var(--primary);">{streak} Days</span>
            </h3>
            <div style="min-width: 600px; margin-top: 15px;">
                {month_labels_html}
                <div style="display: flex; gap: 4px; padding-bottom: 10px;">
                    <div style="display: flex; flex-direction: column; gap: 4px; font-size: 0.7rem; opacity: 0.7; padding-right: 4px; width: 25px; text-align: right;">
                        <div style="height: 14px;"></div>
                        <div style="height: 14px; line-height: 14px;">Mon</div>
                        <div style="height: 14px;"></div>
                        <div style="height: 14px; line-height: 14px;">Wed</div>
                        <div style="height: 14px;"></div>
                        <div style="height: 14px; line-height: 14px;">Fri</div>
                        <div style="height: 14px;"></div>
                    </div>
                    <div style="display: flex; gap: 4px;">
        """
        
        curr = start_date
        while True:
            if curr > end_date and curr.weekday() == 6: 
                break
                
            if curr.weekday() == 6:
                html += '<div style="display: flex; flex-direction: column; gap: 4px;">'
                
            d_str = curr.strftime("%Y-%m-%d")
            
            if curr.year != target_year and curr > end_date:
                color = "transparent"
            elif curr > today:
                color = "rgba(255,255,255,0.02)"
            else:
                color = "var(--primary)" if d_str in login_dates else "rgba(255,255,255,0.05)"
                 
            html += f"<div style='width: 14px; height: 14px; border-radius: 3px; background-color: {color};' title='{d_str}'></div>"
            
            if curr.weekday() == 5: # Saturday
                html += '</div>'
                
            curr += timedelta(days=1)
        
        html += """
                    </div>
                </div>
            </div>
            <p style="opacity: 0.5; font-size: 0.8rem; margin-bottom: 0;">Contribution graph</p>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        
        st.markdown("### 🗑 Account")
        with st.expander("Reset Profile & Start Over"):
            st.warning("⚠️ **WARNING:** This will permanently delete your entire profile, including your roadmaps, tasks, focus sessions, and notes. This action cannot be undone.")
            if st.button("Yes, permanently delete my data", type="primary"):
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


st.markdown("---")
st.markdown("<p style='text-align:center; opacity:0.4; font-size:0.85rem;'>Made with ❤️ by EduNeurons</p>", unsafe_allow_html=True)