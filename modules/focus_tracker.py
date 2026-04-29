import streamlit as st
import streamlit.components.v1 as components
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

    # Fetch mission state early so it's available for saving sessions
    latest_roadmap = storage.get_latest_roadmap(user_id)
    today_task = None
    if latest_roadmap:
        tasks = storage.get_tasks(user_id, latest_roadmap['id'])
        pending = [t for t in tasks if t['status'] == 'pending']
        if pending: today_task = pending[0]

    # \u2500\u2500 TELEMETRY & CONTROL RECEIVER \u2500\u2500
    components.html("""
    <script>
    (function() {
        try {
            // Listen on window.top to catch messages from deep child iframes
            window.top.addEventListener('message', function(event) {
                if (!event.data || !event.data.type) return;
                const pdoc = window.top.document;

                if (event.data.type === 'focus_start') {
                    const input = pdoc.querySelector('input[placeholder="SAMS_START"]');
                    if (input) {
                        input.value = "START_" + event.data.startTime;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }

                if (event.data.type === 'focus_stop') {
                    const input = pdoc.querySelector('input[placeholder="SAMS_STOP"]');
                    if (input) {
                        input.value = JSON.stringify(event.data.data);
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
                
                if (event.data.type === 'focus_sync_heartbeat') {
                    const input = pdoc.querySelector('input[placeholder="SAMS_HEARTBEAT"]');
                    if (input) {
                        input.value = JSON.stringify(event.data.data);
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            });
        } catch(e) { console.warn('SAMS bridge attach error:', e); }
    })();
    </script>
    """, height=0)


    # Inject CSS to keep sync inputs active but invisible
    st.markdown("""
        <style>
        div[data-testid="stTextInput"]:has(input[placeholder="SAMS_START"]),
        div[data-testid="stTextInput"]:has(input[placeholder="SAMS_STOP"]),
        div[data-testid="stTextInput"]:has(input[placeholder="SAMS_HEARTBEAT"]) {
            position: fixed !important;
            top: -100px !important;
            left: -100px !important;
            opacity: 0 !important;
            height: 0 !important;
            width: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Persistence State
    if 'eye_state' not in st.session_state:
        st.session_state.eye_state = {"running": False, "start_time": 0, "score": 100, "counts": {"phone":0,"drowsy":0,"zone_out":0}}

    raw_start = st.text_input("s1", key="s_start", label_visibility="collapsed", placeholder="SAMS_START")
    raw_stop  = st.text_input("s2", key="s_stop",  label_visibility="collapsed", placeholder="SAMS_STOP")
    raw_beat  = st.text_input("s3", key="s_beat",  label_visibility="collapsed", placeholder="SAMS_HEARTBEAT")

    if raw_beat and "{" in raw_beat:
        try:
            beat = json.loads(raw_beat)
            st.session_state.eye_state.update({
                "running": True, "start_time": beat['startTime'], "score": beat['score'], "counts": beat['counts']
            })
        except: pass

    if raw_start and "START_" in raw_start: # Triggered when START is clicked in JS
        st.session_state.eye_state["running"] = True
        st.session_state.eye_state["start_time"] = int(raw_start.split("_")[1])
        from datetime import datetime
        st.session_state.start_time_iso = datetime.now().isoformat()
        st.write('<script>window.parent.document.querySelector("input[placeholder=\'SAMS_START\']").value = "";</script>', unsafe_allow_html=True)

    # ── SESSION SAVING LOGIC ──
    def process_session_save(data):
        try:
            from datetime import datetime
            actual_mins  = data['elapsedMins']
            focus_score  = data['score']
            counts       = data['counts']
            distractions = counts['phone'] + counts['drowsy'] + counts['zone_out']

            storage.save_session(user_id, {
                "task_id":          today_task['id'] if today_task else None,
                "start_time":       st.session_state.get('start_time_iso', datetime.now().isoformat()),
                "end_time":         datetime.now().isoformat(),
                "planned_duration": daily_mins,
                "actual_duration":  actual_mins,
                "focus_score":      focus_score,
                "distraction_count":distractions,
                "drowsy_count":     counts['drowsy'],
                "phone_count":      counts['phone'],
                "zone_out_count":   counts['zone_out'],
                "pause_count":      data.get('pauses', 0),
                "notes":            f"Mission: {today_task['description'] if today_task else 'General'}"
            })

            st.session_state.last_summary = {
                "score": focus_score, "distractions": distractions, "mins": actual_mins
            }
            # RESET STATE to allow fresh start
            st.session_state.eye_state = {"running": False, "start_time": 0, "score": 100, "counts": {"phone":0,"drowsy":0,"zone_out":0}}
            return True
        except Exception as e:
            st.error(f"Save Failed: {str(e)}")
            return False

    # Check Query Params (URL Fallback)
    if "sams_save" in st.query_params:
        try:
            val = st.query_params.get("sams_save")
            if isinstance(val, list): val = val[0]
            if process_session_save(json.loads(val)):
                st.query_params.clear()
                st.rerun()
        except: pass

    # Check PostMessage Hidden Input
    if raw_stop and "{" in raw_stop:
        if process_session_save(json.loads(raw_stop)):
            st.write('<script>window.parent.document.querySelector("input[placeholder=\'SAMS_STOP\']").value = "";</script>', unsafe_allow_html=True)
            st.rerun()

    # ── SIDEBAR: GLOBAL PROGRESS ──
    with st.sidebar:
        ui_helper.render_sidebar_branding()
        
        # 1. My Overall Goals
        ui_helper.render_sidebar_header("My Goals", "📈")
        all_roadmaps = storage.get_all_roadmaps(user_id) or []
        for rm in all_roadmaps:
            tasks = storage.get_tasks(user_id, rm['id']) or []
            done = len([t for t in tasks if t['status'] == 'done'])
            total = len(tasks)
            perc = int((done / total) * 100) if total > 0 else 0
            
            st.markdown(f"""
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                    <span style="font-weight: 600; opacity: 0.9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px;">{rm['goal']}</span>
                    <span style="color: #a855f7; font-weight: 800;">{perc}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(perc / 100)
            
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        
        # 2. Today's Daily Mission (Active Checklist)
        ui_helper.render_sidebar_header("Daily Mission", "🎯")
        
        if latest_roadmap:
            tasks = storage.get_tasks(user_id, latest_roadmap['id']) or []
            pending_tasks = [t for t in tasks if t['status'] == 'pending']
            
            if not tasks:
                st.warning("Roadmap found, but tasks aren't loaded.")
                if st.button("🔄 SYNC TASKS NOW", use_container_width=True):
                    st.session_state.roadmap_mode = "do_commit"
                    st.session_state.temp_roadmap_content = latest_roadmap['content']
                    st.session_state.current_roadmap_id = latest_roadmap['id']
                    st.rerun()
            
            elif pending_tasks:
                curr_w = pending_tasks[0].get('week', 1)
                curr_d = pending_tasks[0].get('day', 1)
                day_tasks = [t for t in tasks if t['week'] == curr_w and t['day'] == curr_d]
                
                st.markdown(f"""
                <div class="eduai-mission-card">
                    <div style="font-size:0.7rem; opacity:0.7; margin-bottom:2px; letter-spacing:1px;">WEEK {curr_w} • DAY {curr_d}</div>
                    <div style="font-size:1rem; font-weight:700; color:#6366f1;">Today's Target</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<div style='margin-top:15px; margin-bottom:10px;'></div>", unsafe_allow_html=True)
                
                for t in day_tasks:
                    is_done = (t['status'] == 'done')
                    if st.checkbox(t['description'], value=is_done, key=f"side_task_{t['id']}"):
                        if not is_done:
                            storage.update_task_status(t['id'], 'done')
                            st.rerun()
                    
                if all(t['status'] == 'done' for t in day_tasks):
                    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
                    if st.button("🌟 DAY COMPLETE!", use_container_width=True, type="primary"):
                        st.balloons()
                        st.rerun()
            else:
                st.success("All tasks complete! 🎉")
        else:
            st.warning("No active roadmap.")
        
        st.markdown("---")
        st.markdown("### 🏆 Recent History")
        
        # FAILSAFE: Manual Management Buttons
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            # Prevent impossible times by checking if session is running and has valid start time
            is_active = st.session_state.eye_state.get('running', False)
            if st.button("🔃 FORCE SAVE", help="Manually save current AI stats", use_container_width=True):
                s = st.session_state.eye_state
                start_ms = s.get('start_time', 0)
                
                # If start_time is 0 or extremely small (not a valid epoch), it's an invalid session
                if not is_active or start_ms < 1000000000000: # Threshold for modern ms timestamp
                    st.error("No active session detected.")
                else:
                    actual_mins = max(1, int((time.time()*1000 - start_ms)/60000))
                    storage.save_session(user_id, {
                        "task_id":          None,
                        "start_time":       st.session_state.get('start_time_iso', "Just now"),
                        "end_time":         "Manual Stop",
                        "planned_duration": 0,
                        "actual_duration":  actual_mins,
                        "focus_score":      s.get('score', 100),
                        "distraction_count":sum(s['counts'].values()) if 'counts' in s else 0,
                        "drowsy_count":     s.get('counts',{}).get('drowsy',0),
                        "phone_count":      s.get('counts',{}).get('phone',0),
                        "zone_out_count":   s.get('counts',{}).get('zone_out',0),
                        "pause_count":      0,
                        "notes":            "Manual Force Save"
                    })
                    st.success("Saved!")
                    st.rerun()
        with col_s2:
            if st.button("🗑️ CLEAR", help="Clear current session memory", use_container_width=True):
                st.session_state.eye_state = {"running": False, "start_time": 0, "score": 100, "counts": {"phone":0,"drowsy":0,"zone_out":0}}
                st.rerun()

        sessions = storage.get_sessions(user_id)
        for s in sessions[:3]:
            st.markdown(f'<div class="eduai-session-badge">⏱ {s["actual_duration"]}m | {s["focus_score"]}% Focus</div>', unsafe_allow_html=True)

    # ── MAIN: FOCUS MONITOR ──
    st.markdown("<h1 style='text-align:center;'>Mission Control: Focus Guard</h1>", unsafe_allow_html=True)
    
    if st.session_state.get('last_summary'):
        s = st.session_state.last_summary
        st.success(f"🏁 Session Saved! Score: **{s['score']}%** | Distractions: **{s['distractions']}** | Duration: **{s['mins']}m**")
        if st.button("Dismiss"):
            del st.session_state.last_summary
            st.rerun()

    col_left, col_mid, col_right = st.columns([1, 6, 1])
    with col_mid:
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        guard_on = st.checkbox("🛰️ CONNECT FOCUS GUARD", value=True, help="Toggle AI Distraction Detection. Timer always stays active.")
        eye_tracker.embed_eye_tracker(initial_mins=daily_mins, state=st.session_state.eye_state, guard_enabled=guard_on)

    # Mission control is now handled inside the JS component.
    # No more Python-side timer loop to prevent refreshing/blinking.

    # ── JS REPOSITIONING FOR HUD ──
    components.html("""
    <script>
    (function() {
        function tagHUD() {
            var pdoc = window.parent.document;
            var marker = pdoc.getElementById('mission-control-marker');
            if (marker) {
                var container = marker.closest('[data-testid="stVerticalBlock"]');
                if (container && !container.classList.contains('eduai-mission-control')) {
                    container.classList.add('eduai-mission-control');
                    container.style.display = 'block';
                }
            } else { setTimeout(tagHUD, 100); }
        }
        tagHUD();
    })();
    </script>
    """, height=0)

    # ── POST-SESSION SUMMARY ──
    if st.session_state.get("last_summary"):
        s = st.session_state.last_summary
        msg = "Outstanding work, Commander!" if s['score'] > 80 else "Steady progress. Let's aim higher next time."
        st.markdown(f"""
        <div class="eduai-mission-card" style="text-align:center; margin-top:40px;">
            <div style="font-size:2rem; margin-bottom:10px;">📊 Mission Debrief</div>
            <div style="font-size:1.5rem; font-weight:700; color:#6366f1;">Focus Score: {s['score']}%</div>
            <div style="margin:10px 0;">You stayed focused for {s['mins']} minutes with {s['distractions']} distractions.</div>
            <div style="font-style:italic; opacity:0.7;">"{msg}"</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 DISMISS & RESET FOR NEXT MISSION", use_container_width=True, type="primary"):
            del st.session_state.last_summary
            st.rerun()

    # Active update loop removed. UI updates are handled in JS.