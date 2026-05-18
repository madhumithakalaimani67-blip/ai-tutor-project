import streamlit as st
from utils import storage

def main(user_id, user_profile):
    
    # Pre-compute metrics to show in Hero
    sessions = storage.get_sessions(user_id)
    streak = storage.get_streak(user_id)
    total_mins = sum([s["actual_duration"] for s in sessions]) if sessions else 0
    
    current_rm_id = st.session_state.get("current_roadmap_id")
    active_roadmap = storage.get_roadmap_by_id(user_id, current_rm_id) if current_rm_id else storage.get_latest_roadmap(user_id)
    progress_perc = 0
    tasks = []
    if active_roadmap:
        tasks = storage.get_tasks(user_id, active_roadmap['id']) or []
        if tasks:
            done = len([t for t in tasks if t['status'] == 'done'])
            progress_perc = round((done / len(tasks)) * 100, 1)

    # --- HERO LANDING SECTION ---
    hero_col_text, hero_col_img = st.columns([1.2, 1])
        
    with hero_col_text:
        st.markdown(f"<h1 style='font-size: 3.2rem; margin-bottom: 5px;'>Welcome back, {user_profile.get('name', 'Learner')} 👋</h1>", unsafe_allow_html=True)
        
        # --- DISPLAY PRIMARY GOAL ---
        goal = user_profile.get('primary_goal', 'No goal set yet.')
        st.markdown(f"""
            <div style="background: rgba(var(--primary-rgb), 0.1); border-left: 5px solid var(--primary); padding: 15px 20px; border-radius: 10px; margin-bottom: 20px;">
                <p style="margin:0; font-size: 0.9rem; opacity: 0.6; text-transform: uppercase; letter-spacing: 1px;">Current Objective</p>
                <h3 style="margin:0; font-size: 1.4rem; color: white;">{goal}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"<p style='font-size: 1.15rem; opacity: 0.8; margin-bottom: 25px;'>Your dedicated AI workspace is ready. Stay focused, track your progress, and master your path.</p>", unsafe_allow_html=True)
        
        if active_roadmap:
            next_task = next((t for t in tasks if t['status'] == 'pending'), None)
            if next_task:
                st.error(f"🎯 **NEXT MISSION:** {next_task['description'][:60]}...")
                if st.button("🚀 RESUME JOURNEY", use_container_width=False, type="primary", key="dash_hero_btn_resume"):
                    st.session_state.navigate_to = "Focus Timer"
                    st.rerun()
            else:
                st.success("🎉 **ALL MISSIONS COMPLETE!**")
                if st.button("🛣️ BUILD NEW PATH", type="primary", key="dash_new_path"):
                    st.session_state.navigate_to = "Roadmap"
                    st.rerun()
        else:
            st.info("Start by generating your first AI Roadmap!")
            if st.button("🛣️ MAP YOUR PATH", use_container_width=False, type="primary", key="dash_hero_btn_map"):
                st.session_state.navigate_to = "Roadmap"
                st.rerun()
                
    with hero_col_img:
        import os
        if os.path.exists(os.path.join("assets", "dashboard_hero.png")):
            st.image(os.path.join("assets", "dashboard_hero.png"), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- CORE METRICS RENDERED UNDER HERO ---
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown(f"""
            <h3 style="margin-top:0;"> 🕒 Total Focus</h3>
            <h2 style="margin-bottom:0;">{total_mins}m</h2>
            <p style="opacity:0.6;">Great work!</p>
            """, unsafe_allow_html=True)
    with col2:
        with st.container(border=True):
            st.markdown(f"""
            <h3 style="margin-top:0;">🔥 Streak</h3>
            <h2 style="margin-bottom:0;">{streak} Days</h2>
            <p style="opacity:0.6;">Keep it up!</p>
            """, unsafe_allow_html=True)
    with col3:
        with st.container(border=True):
            st.markdown(f"""
            <h3 style="margin-top:0;">🚀 Progress</h3>
            <h2 style="margin-bottom:0;">{progress_perc}%</h2>
            <p style="opacity:0.6;">Goal: {active_roadmap['goal'][:15] if active_roadmap else 'None'}</p>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main(None, {})
