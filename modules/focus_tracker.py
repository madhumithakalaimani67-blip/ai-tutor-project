import streamlit as st
import time
import json
from utils import storage, ui_helper
from modules import eye_tracker

def get_daily_mins(s):
    if "30 mins"  in s: return 30
    if "1 hour"   in s: return 60
    if "2 hours"  in s: return 120
    if "3+ hours" in s: return 180
    return 25

def main(user_id):
    user_profile = st.session_state.get('user_profile', {})
    daily_mins   = get_daily_mins(user_profile.get('daily_time', '1 hour'))

    main_col = st.container()

    # ── SIDEBAR Branding & Navigation ──
    with st.sidebar:
        ui_helper.render_sidebar_branding()
        st.markdown("## ⏱️ Focus")
        st.markdown(f"**🎯 Target:** {daily_mins} mins today")
        st.markdown("---")
        st.markdown("**🏆 Recent Sessions**")
        sessions = storage.get_sessions(user_id)
        if sessions:
            for s in sessions[:5]:
                with st.expander(f"📅 {s['start_time'][4:16]}"):
                    st.write(f"⏱ **{s['actual_duration']}m** | 🎯 **{s['focus_score']}%**")
        else:
            st.caption("No sessions yet!")
        st.markdown("---")
        st.info("💡 Enable Focus Guard for eye tracking.")

    # ── MAIN ──
    with main_col:
        st.title("⏱ Disciplined Focus Hub")
        st.markdown("### 📋 Your Daily Missions")

        latest_roadmap = storage.get_latest_roadmap(user_id)
        today_task = None

        if latest_roadmap:
            tasks = storage.get_tasks(user_id, latest_roadmap['id'])
            pending = [t for t in tasks if t['status'] == 'pending']
            if pending:
                today_task = pending[0]
                st.info(f"🚨 **TODAY:** {today_task['description']}")
                try:
                    steps = json.loads(today_task.get('breakdown','[]'))
                    if steps:
                        st.markdown("### ✅ Checklist")
                        all_done = True
                        for i, step in enumerate(steps, 1):
                            if not st.checkbox(step, key=f"step_{today_task['id']}_{i}"):
                                all_done = False
                        if all_done:
                            st.success("🎉 All done!")
                            st.balloons()
                            if st.button("Complete & Go to Dashboard", type="primary", use_container_width=True):
                                storage.update_task_status(today_task['id'], 'done')
                                st.session_state.navigate_to = "Dashboard"
                                st.rerun()
                except: pass
            else:
                st.success("✅ All missions completed!")
                if st.button("🗺️ New Roadmap", use_container_width=True):
                    st.session_state.navigate_to = "Roadmap"
                    st.rerun()
        else:
            st.warning("⚠️ No active roadmap.")
            if st.button("🛠️ Generate Roadmap", use_container_width=True):
                st.session_state.navigate_to = "Roadmap"
                st.rerun()

        col_main, col_info = st.columns([2, 1])
        with col_info:
            st.markdown("### 🎯 Session Info")
            st.write(f"**Target:** {daily_mins} mins")

        with col_main:
            if "timer_running" not in st.session_state: st.session_state.timer_running = False
            if "is_paused"     not in st.session_state: st.session_state.is_paused     = False

            st.markdown("---")
            if st.toggle("🛡️ Enable Focus Guard", value=False, key="eye_guard_toggle"):
                eye_tracker.embed_eye_tracker()
            st.markdown("---")

            if not st.session_state.timer_running:
                if st.button("🚀 START SESSION", use_container_width=True, key="btn_start"):
                    st.session_state.timer_running        = True
                    st.session_state.is_paused            = False
                    st.session_state.start_time           = time.time()
                    st.session_state.pause_count          = 0
                    st.session_state.total_pause_duration = 0
                    st.rerun()
            else:
                c_p, c_s = st.columns(2)
                with c_p:
                    if not st.session_state.is_paused:
                        if st.button("⏸ PAUSE", use_container_width=True, key="btn_pause"):
                            st.session_state.is_paused   = True
                            st.session_state.pause_start = time.time()
                            st.session_state.pause_count = st.session_state.get("pause_count",0)+1
                            st.rerun()
                    else:
                        if st.button("▶️ RESUME", use_container_width=True, key="btn_resume"):
                            st.session_state.is_paused            = False
                            st.session_state.total_pause_duration += time.time()-st.session_state.pause_start
                            st.rerun()
                with c_s:
                    if st.button("⏹ STOP & SAVE", use_container_width=True, key="btn_stop"):
                        elapsed     = (time.time()-st.session_state.start_time)-st.session_state.get("total_pause_duration",0)
                        actual_mins = int(elapsed//60)
                        focus_score = max(0, 95-(st.session_state.get("pause_count",0)*5))
                        storage.save_session(user_id,{
                            "task_id":          today_task['id'] if today_task else None,
                            "start_time":       time.ctime(st.session_state.start_time),
                            "end_time":         time.ctime(),
                            "planned_duration": daily_mins,
                            "actual_duration":  actual_mins,
                            "focus_score":      focus_score,
                            "pause_count":      st.session_state.get("pause_count",0),
                            "notes":            f"Mission: {today_task['description'] if today_task else 'General'}"
                        })
                        if today_task:
                            storage.update_task_status(today_task['id'],'done')
                            st.balloons()
                        st.session_state.timer_running = False
                        st.rerun()

                if st.session_state.timer_running:
                    elapsed   = int(time.time()-st.session_state.start_time)-int(st.session_state.get("total_pause_duration",0))
                    if st.session_state.is_paused:
                        elapsed = int(st.session_state.pause_start-st.session_state.start_time)-int(st.session_state.get("total_pause_duration",0))
                    remaining = max(0,(daily_mins*60)-elapsed)
                    if st.session_state.is_paused:
                        st.markdown("<h1 style='text-align:center;color:#f59e0b;font-size:5rem;'>⏸ PAUSED</h1>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<h1 style='text-align:center;font-size:7rem;margin:0;'>{remaining//60:02}:{remaining%60:02}</h1>", unsafe_allow_html=True)
                    st.progress(min(1.0, elapsed/(daily_mins*60)))
                    if not st.session_state.is_paused and remaining > 0:
                        time.sleep(1); st.rerun()