import streamlit as st
import time
import json
from utils import storage, ai_helper
from modules import eye_tracker

def get_daily_mins(daily_time_str):
    if "30 mins" in daily_time_str: return 30
    if "1 hour" in daily_time_str: return 60
    if "2 hours" in daily_time_str: return 120
    if "3+ hours" in daily_time_str: return 180
    return 25

def main(user_id):
    st.title("⏱ Disciplined Focus Hub")
    
    user_profile = st.session_state.get('user_profile', {})
    daily_mins = get_daily_mins(user_profile.get('daily_time', '1 hour'))

    # --- MISSION SELECTION & CHECKBOX ---
    st.markdown("### 📋 Your Daily Missions")
    latest_roadmap = storage.get_latest_roadmap(user_id)
    today_task = None
    
    if latest_roadmap:
        tasks = storage.get_tasks(user_id, latest_roadmap['id'])
        pending_tasks = [t for t in tasks if t['status'] == 'pending']
        
        if pending_tasks:
            # Checkbox List for Selection
            selected_task_desc = None
            for p in pending_tasks:
                if st.checkbox(f"🎯 {p['description']}", key=f"mission_{p['id']}"):
                    selected_task_desc = p['description']
                    today_task = p
            
            if today_task:
                st.info(f"⏳ **Current Focus:** {today_task['description']}")
                
                # --- THE VAULT: FETCH REAL BREAKDOWN FROM DB ---
                breakdown_text = today_task.get('breakdown', '[]')
                try:
                    steps = json.loads(breakdown_text)
                    if steps:
                        with st.expander("📓 The Vault - Mission Breakdown", expanded=True):
                            for i, step in enumerate(steps, 1):
                                st.markdown(f"{i}. **{step}**")
                except: pass
            else:
                st.caption("👈 Tick a checkbox to set your active mission.")
        else:
            st.success("✅ All missions from your current roadmap are completed!")
            if st.button("🗺️ Create New Roadmap", use_container_width=True):
                st.session_state.menu_choice = "Roadmap"
                st.rerun()
    else:
        st.warning("⚠️ No active roadmap found.")
        if st.button("🛠️ Generate First Roadmap", use_container_width=True):
            st.session_state.menu_choice = "Roadmap"
            st.rerun()

    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.info("💡 Start a session and use the Focus Guard below to stay on track.")
        
        st.markdown("---")
        st.markdown("### 🏆 History")
        sessions = storage.get_sessions(user_id)
        if sessions:
            for s in sessions[:5]:
                st.caption(f"📅 {s['start_time'][5:16]} - {s['actual_duration']}m")

    # TIMER DISPLAY
    col_main, col_info = st.columns([2, 1])

    with col_info:
        st.markdown("### 🎯 Session Info")
        st.write(f"**Target:** {daily_mins} mins")
        if st.session_state.get("pause_count", 0) >= 2:
            st.warning("⚠️ **Stay strong!** Pausing breaks your momentum.")

    with col_main:
        if "timer_running" not in st.session_state: st.session_state.timer_running = False
        if "is_paused" not in st.session_state: st.session_state.is_paused = False

        # --- EYE TRACKER TOGGLE ---
        st.markdown("---")
        enable_guard = st.toggle("🛡️ Enable Focus Guard (Eye Tracking + PiP)", value=False, key="eye_guard_toggle")
        if enable_guard:
            eye_tracker.embed_eye_tracker()
        st.markdown("---")

        if not st.session_state.timer_running:
            if st.button("🚀 START FIXED SESSION", use_container_width=True, key="btn_start"):
                st.session_state.timer_running = True
                st.session_state.is_paused = False
                st.session_state.start_time = time.time()
                st.session_state.pause_count = 0
                st.session_state.total_pause_duration = 0
                st.rerun()
        else:
            c_p, c_s = st.columns(2)
            with c_p:
                if not st.session_state.is_paused:
                    if st.button("⏸ PAUSE", use_container_width=True, key="btn_pause"):
                        st.session_state.is_paused = True
                        st.session_state.pause_start = time.time()
                        st.session_state.pause_count = st.session_state.get("pause_count", 0) + 1
                        st.rerun()
                else:
                    if st.button("▶️ RESUME", use_container_width=True, key="btn_resume"):
                        st.session_state.is_paused = False
                        st.session_state.total_pause_duration += (time.time() - st.session_state.pause_start)
                        st.rerun()
            with c_s:
                if st.button("⏹ STOP & SAVE", use_container_width=True, key="btn_stop"):
                    final_elapsed = (time.time() - st.session_state.start_time) - st.session_state.get("total_pause_duration", 0)
                    actual_mins = int(final_elapsed // 60)
                    focus_score = 95 - (st.session_state.get("pause_count", 0) * 5)
                    
                    storage.save_session(user_id, {
                        "task_id": today_task['id'] if today_task else None,
                        "start_time": time.ctime(st.session_state.start_time),
                        "end_time": time.ctime(),
                        "planned_duration": daily_mins,
                        "actual_duration": actual_mins,
                        "focus_score": max(0, int(focus_score)),
                        "pause_count": st.session_state.get("pause_count", 0),
                        "notes": f"Mission: {today_task['description'] if today_task else 'General'}"
                    })
                    
                    if today_task:
                        storage.update_task_status(today_task['id'], 'done')
                        st.balloons()

                    st.session_state.timer_running = False
                    st.rerun()

            if st.session_state.timer_running:
                if st.session_state.is_paused:
                    elapsed = int(st.session_state.pause_start - st.session_state.start_time) - int(st.session_state.total_pause_duration)
                else:
                    elapsed = int(time.time() - st.session_state.start_time) - int(st.session_state.total_pause_duration)
                
                remaining = max(0, (daily_mins * 60) - elapsed)
                if st.session_state.is_paused:
                    st.markdown("<h1 style='text-align: center; color: #f59e0b; font-size: 6rem; margin: 0;'>⏸ PAUSED</h1>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<h1 style='text-align: center; font-size: 8rem; margin: 0;'>{remaining // 60:02}:{remaining % 60:02}</h1>", unsafe_allow_html=True)
                
                st.progress(min(1.0, elapsed / (daily_mins * 60)))
                if not st.session_state.is_paused and remaining > 0:
                    time.sleep(1); st.rerun()


if __name__ == "__main__":
    main(None)
