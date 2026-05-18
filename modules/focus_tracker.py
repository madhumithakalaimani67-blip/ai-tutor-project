import streamlit as st
import streamlit.components.v1 as components
import time
import json
from utils import storage, ui_helper
from modules import eye_tracker
from datetime import datetime





def get_session_duration(today_task, user_profile):
    """Parses duration from roadmap task or falls back to user settings."""
    import re
    
    # 1. Try Roadmap Task Description
    if today_task:
        desc = today_task.get('description', '') 
        # Pattern: (1 hour), (30 mins), (2hr)
        match = re.search(r'\((\d+)\s*(hour|hr|min|minutes)', desc, re.I)
        if match:
            val = int(match.group(1))
            unit = match.group(2).lower()
            if 'hour' in unit or 'hr' in unit:
                return val * 60, "roadmap"
            return val, "roadmap"
            
    # 2. Fallback to User Settings
    user_profile = user_profile or {}
    daily_str = user_profile.get('daily_time', '1 hour')
    match = re.search(r'(\d+)', daily_str)
    if match:
        val = int(match.group(1))
        if 'hour' in daily_str.lower():
            return val * 60, "settings"
        return val, "settings"
        
    return 25, "default"

def get_total_weeks(tasks):
    """Get the maximum week number from all tasks."""
    if not tasks:
        return 1
    return max([t.get('week', 1) for t in tasks])

def main(user_id):
    user_profile = st.session_state.get('user_profile', {})

    # Fetch mission state early so it's available for saving sessions
    current_rm_id = st.session_state.get("current_roadmap_id")
    active_roadmap = storage.get_roadmap_by_id(user_id, current_rm_id) if current_rm_id else storage.get_latest_roadmap(user_id)
    today_task = None
    if active_roadmap:
        tasks = storage.get_tasks(user_id, active_roadmap['id'])
        
        # One-time migration: fix global day numbering to week-relative
        if not st.session_state.get(f'days_fixed_{active_roadmap["id"]}'):
            storage.fix_task_day_numbering(user_id)
            st.session_state[f'days_fixed_{active_roadmap["id"]}'] = True
            tasks = storage.get_tasks(user_id, active_roadmap['id'])  # re-fetch after fix
            # Clear nav state so it re-initializes from corrected day numbers
            for k in [f'nav_w_{active_roadmap["id"]}', f'nav_d_{active_roadmap["id"]}']:
                if k in st.session_state: del st.session_state[k]
        
        pending = [t for t in tasks if t['status'] == 'pending']
        if pending: today_task = pending[0]

    # Calculate baseline session duration early
    planned_mins, duration_source = get_session_duration(today_task, user_profile)

    # ── TELEMETRY & CONTROL BRIDGE ──
    # Most sync logic (Heartbeats, Stop/Save) is handled globally in app.py
    # via ui_helper.render_focus_sync_background() to ensure persistence across all modules.
    
    # Session handling (Start, Save, Sync) is managed globally in ui_helper.py




    # Inject CSS to keep sync inputs active but invisible
    st.markdown("""
        <style>
        div[data-testid="stTextInput"]:has(input[placeholder="SAMS_START"]),
        div[data-testid="stTextInput"]:has(input[placeholder="SAMS_HEARTBEAT"]) {
            position: fixed !important;
            top: -100px !important;
            left: -100px !important;
            opacity: 0 !important;
            height: 0 !important;
            width: 0 !important;
        }
        
        .nav-button-locked {
            opacity: 0.4 !important;
            cursor: not-allowed !important;
            color: #666666 !important;
            background: rgba(100,100,100,0.2) !important;
            border-color: rgba(100,100,100,0.3) !important;
        }

        .nav-button-locked:hover {
            opacity: 0.4 !important;
            background: rgba(100,100,100,0.2) !important;
        }

        .nav-button-unlocked {
            opacity: 1 !important;
            cursor: pointer !important;
            color: #e2e8f0 !important;
            background: rgba(99,102,241,0.1) !important;
            border-color: rgba(99,102,241,0.3) !important;
            transition: all 0.3s ease !important;
        }

        .nav-button-unlocked:hover {
            opacity: 1 !important;
            background: rgba(99,102,241,0.2) !important;
            border-color: rgba(99,102,241,0.5) !important;
        }
        div[data-testid="stTextInput"]:has(input[placeholder="SAMS_TEL"]) {
            position: fixed !important; top: -200px !important;
            opacity: 0 !important; pointer-events: none !important;
            height: 0 !important; width: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)


    # Persistence State
    if 'eye_state' not in st.session_state:
        st.session_state.eye_state = {"running": False, "start_time": 0, "score": 100, "counts": {"phone":0,"drowsy":0,"zone_out":0}}
    
    # Restore from persistent state if session was running before navigation
    if st.session_state.get('persistent_eye_state', {}).get('running', False):
        st.session_state.eye_state = st.session_state.persistent_eye_state.copy()

    # Session handling is managed globally in ui_helper.py

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
            is_active = (current_rm_id == rm['id']) if current_rm_id else (active_roadmap and active_roadmap['id'] == rm['id'])
            perc = round((done / total) * 100, 1) if total > 0 else 0
            btn_label = f"{'🎯 ' if is_active else ''}{rm['goal'][:15]}... ({perc}%)"
            
            if st.button(btn_label, key=f"goal_btn_{rm['id']}", use_container_width=True):
                st.session_state.current_roadmap_id = rm['id']
                st.rerun()
            st.progress(perc / 100)
            
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        
        # 2. Today's Daily Mission (Active Checklist)
        ui_helper.render_sidebar_header("Daily Mission", "🎯")
        
        if active_roadmap:
            tasks = storage.get_tasks(user_id, active_roadmap['id']) or []
            pending_tasks = [t for t in tasks if t['status'] == 'pending']
            
            if not tasks:
                st.warning("Roadmap found, but tasks aren't loaded.")
                if st.button("🔄 SYNC TASKS NOW", use_container_width=True):
                    import re
                    content = active_roadmap.get('content', '')
                    tasks_to_save = []
                    current_w, current_d = 1, 1
                    for line in content.split('\n'):
                        line = line.strip()
                        if not line: continue
                        w_match = re.search(r'\b(?:Week|WEEK)\s+(\d+)\b', line, re.IGNORECASE)
                        if w_match and len(line) < 30:
                            current_w = int(w_match.group(1)); continue
                        d_match = re.search(r'\b(?:Day|DAY)\s+(\d+)\b', line, re.IGNORECASE)
                        if d_match and len(line) < 30:
                            current_d = int(d_match.group(1)); continue
                        
                        is_task = line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line)
                        if not is_task and (line.lower().startswith('technical') or line.lower().startswith('non-technical') or line.lower().startswith('task')):
                            is_task = True
                            
                        if is_task:
                            task_desc = re.sub(r'^[\-\*\d\.\s]+', '', line).strip()
                            task_desc = re.sub(r'^(?:Technical|Non-Technical|Task)[\w\s]*:\s*', '', task_desc, flags=re.IGNORECASE).strip()
                            task_desc = task_desc.replace('**','').replace('*','')
                            if task_desc:
                                tasks_to_save.append({'week': current_w, 'day': current_d, 'task': task_desc[:150], 'subtasks': []})
                    if tasks_to_save:
                        storage.save_tasks(user_id, active_roadmap['id'], tasks_to_save)
                        st.success(f"✅ Synced {len(tasks_to_save)} tasks!")
                        st.rerun()
                    else:
                        st.error("Could not extract tasks. The roadmap format may be invalid. Try regenerating it.")

            
            elif tasks:
                pending_tasks = [t for t in tasks if t['status'] == 'pending']
                # Determine baseline day: first pending task or last task if all done
                if pending_tasks:
                    base_w = pending_tasks[0].get('week', 1)
                    base_d = pending_tasks[0].get('day', 1)
                else:
                    base_w = tasks[-1].get('week', 1)
                    base_d = tasks[-1].get('day', 1)

                # Initialize navigation state if not present
                if f"nav_w_{active_roadmap['id']}" not in st.session_state:
                    st.session_state[f"nav_w_{active_roadmap['id']}"] = base_w
                    st.session_state[f"nav_d_{active_roadmap['id']}"] = base_d

                curr_w = st.session_state[f"nav_w_{active_roadmap['id']}"]
                curr_d = st.session_state[f"nav_d_{active_roadmap['id']}"]

                # Render Navigator
                new_week, new_day = ui_helper.render_daily_mission_navigator(
                    user_id=user_id,
                    current_week=curr_w,
                    current_day=curr_d,
                    all_tasks=tasks,
                    total_weeks=get_total_weeks(tasks)
                )

                if (new_week, new_day) != (curr_w, curr_d):
                    st.session_state[f"nav_w_{active_roadmap['id']}"] = new_week
                    st.session_state[f"nav_d_{active_roadmap['id']}"] = new_day
                    st.rerun()

                # Display tasks for the selected day
                day_tasks = [t for t in tasks if t['week'] == curr_w and t['day'] == curr_d]
                
                st.markdown(f"""
                <div class="eduai-mission-card" style="padding: 15px; margin-top: 10px;">
                    <div style="font-size:1rem; font-weight:700; color:#6366f1;">Today's Target</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<div style='margin-top:10px; margin-bottom:10px;'></div>", unsafe_allow_html=True)
                
                for t in day_tasks:
                    is_done = (t['status'] == 'done')
                    if st.checkbox(t['description'], value=is_done, key=f"side_task_{t['id']}"):
                        if not is_done:
                            storage.update_task_status(t['id'], 'done')
                            st.rerun()
                    

                if day_tasks and all(t['status'] == 'done' for t in day_tasks):
                    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
                    st.markdown("""
                        <div style="text-align: center; color: #10b981; font-weight: 700; font-size: 0.9rem; padding: 10px; background: rgba(16, 185, 129, 0.1); border-radius: 10px;">
                            🌟 DAY COMPLETE!
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Auto-trigger balloons once per day
                    balloons_key = f"balloons_{active_roadmap['id']}_{curr_w}_{curr_d}"
                    if balloons_key not in st.session_state:
                        st.balloons()
                        storage.record_login(st.session_state.user_id)
                        st.session_state[balloons_key] = True
            else:
                st.success("All tasks complete! 🎉")
        else:
                  st.markdown("---")

        # Step 1: Read tel from URL if present (set by previous click)
        import base64 as _b64
        _tel_param = st.query_params.get('savtel', '')
        if _tel_param:
            try:
                _tel = json.loads(_b64.b64decode(_tel_param + '==').decode())
                st.session_state['js_tel'] = _tel
                
                # Automatically save the session right now to avoid a second click!
                js_tel = _tel
                phone    = int(js_tel.get('phone', 0))
                drowsy   = int(js_tel.get('drowsy', 0))
                zone_out = int(js_tel.get('zone_out', 0))
                pauses   = int(js_tel.get('pauses', 0))
                distractions = phone + drowsy + zone_out
                focus_score  = max(0, 100 - phone*5 - drowsy*5 - zone_out*5 - pauses*2)

                start_iso = st.session_state.get('start_time_iso') or datetime.now().isoformat()
                try:
                    elapsed = max(1, round(float(js_tel.get('elapsedMins', 1)), 1))
                except:
                    elapsed = 1

                storage.save_session(user_id, {
                    "task_id":           today_task['id'] if today_task else None,
                    "start_time":        start_iso,
                    "end_time":          datetime.now().isoformat(),
                    "planned_duration":  int(planned_mins),
                    "actual_duration":   elapsed,
                    "focus_score":       int(focus_score),
                    "distraction_count": distractions,
                    "phone_count":       phone,
                    "drowsy_count":      drowsy,
                    "zone_out_count":    zone_out,
                    "pause_count":       pauses,
                    "notes":             f"Mission: {today_task['description'] if today_task else 'General'}"
                })
                st.session_state.last_summary = {
                    "score": int(focus_score), "distractions": distractions, "mins": elapsed
                }
                st.session_state.start_time_iso = None
                st.session_state['js_tel'] = {}
                st.session_state.eye_state = {
                    "running": False, "start_time": 0, "score": 100,
                    "counts": {"phone": 0, "drowsy": 0, "zone_out": 0}
                }
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                print(f"[AUTOSAVE ERROR] {e}")

        # Step 2: Show save button
        if st.button("🏁 Save Session", key="sidebar_save_btn",
                     use_container_width=True, type="primary"):
            st.info("**Click 'Save Session' again** to confirm and save.", icon="👆")
            
            # Inject JS to read localStorage and set URL param, then rerun
            components.html("""
            <script>
            (function() {
                try {
                    var tel = window.top.localStorage.getItem('sams_final_tel') || '{}';
                    var encoded = btoa(unescape(encodeURIComponent(tel)));
                    
                    // Write to URL without navigation
                    var url = new URL(window.top.location.href);
                    url.searchParams.set('savtel', encoded);
                    window.top.history.replaceState(null, '', url.toString());
                    
                    // Force Streamlit to rerun by triggering the hidden input with value change
                    setTimeout(function() {
                        var inputs = window.parent.document.querySelectorAll('input');
                        inputs.forEach(function(inp) {
                            if (inp.placeholder === 'SAMS_START') {
                                var setter = Object.getOwnPropertyDescriptor(
                                    window.HTMLInputElement.prototype, 'value').set;
                                setter.call(inp, 'RERUN_' + Date.now());
                                inp.dispatchEvent(new Event('input', { bubbles: true }));
                            }
                        });
                    }, 100);
                } catch(e) { console.error('savtel error:', e); }
            })();
            </script>
            """, height=0)



        # Recent Sessions — delegated to ui_helper
        ui_helper.render_sidebar_recent_sessions(user_id)





    # ── MAIN: FOCUS MONITOR ──
    st.markdown("""
        <div style="background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); padding: 12px; border-radius: 12px; margin-bottom: 20px; text-align: center;">
            <span style="color: #fbbf24; font-weight: 700;">⚠️ NAVIGATION NOTICE:</span> 
            <span style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">
                For the best accuracy, please avoid switching between internal modules (Roadmap, Doubt Solver, etc.) while the timer is running. 
                <b>You may freely use other apps, browser tabs, or PiP mode.</b>
            </span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
<div style="display:flex; justify-content:center; gap:12px; margin-bottom:16px; flex-wrap:wrap;">
    <div style="background:rgba(6,182,212,0.1); border:1px solid rgba(6,182,212,0.3); 
                border-radius:12px; padding:10px 18px; text-align:center;">
        <div style="font-size:1.2rem;">▶️</div>
        <div style="font-size:0.75rem; font-weight:700; color:#06b6d4; margin-top:4px;">STEP 1</div>
        <div style="font-size:0.8rem; color:#cbd5e1;">Click START to begin</div>
    </div>
    <div style="color:#475569; font-size:1.2rem; align-self:center;">→</div>
    <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); 
                border-radius:12px; padding:10px 18px; text-align:center;">
        <div style="font-size:1.2rem;">⏹️</div>
        <div style="font-size:0.75rem; font-weight:700; color:#ef4444; margin-top:4px;">STEP 2</div>
        <div style="font-size:0.8rem; color:#cbd5e1;">Click STOP when done</div>
    </div>
    <div style="color:#475569; font-size:1.2rem; align-self:center;">→</div>
    <div style="background:rgba(168,85,247,0.1); border:1px solid rgba(168,85,247,0.3); 
                border-radius:12px; padding:10px 18px; text-align:center;">
        <div style="font-size:1.2rem;">🏁</div>
        <div style="font-size:0.75rem; font-weight:700; color:#a855f7; margin-top:4px;">STEP 3</div>
        <div style="font-size:0.8rem; color:#cbd5e1;">Click Save Session in sidebar</div>
    </div>
</div>
""", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;'>Mission Control: Focus Guard</h1>", unsafe_allow_html=True)
    
    # ── POST-SESSION SUMMARY (MOVE TO TOP) ──
    if st.session_state.get("last_summary"):
        s = st.session_state.last_summary
        msg = "Outstanding work, Commander!" if s['score'] > 80 else "Steady progress. Let's aim higher next time."
        st.markdown(f"""
        <div class="eduai-mission-card" style="text-align:center; margin-top:20px; border-color: #10b981; background: rgba(16, 185, 129, 0.05);">
            <div style="font-size:1.8rem; margin-bottom:10px;">📊 Mission Debrief</div>
            <div style="font-size:1.5rem; font-weight:700; color:#10b981;">Focus Score: {s['score']}%</div>
            <div style="margin:10px 0;">You stayed focused for {round(s['mins'], 1)} minutes with {s['distractions']} distractions.</div>
            <div style="font-style:italic; opacity:0.7;">"{msg}"</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 DISMISS & START NEW MISSION", use_container_width=True, type="primary"):
            del st.session_state.last_summary
            st.rerun()
        st.stop() # Stop here to hide the tracker while showing results
    
    col_left, col_mid, col_right = st.columns([1, 6, 1])
    with col_mid:
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        
        # Determine duration: use stored one if running to prevent reset on navigate
        if st.session_state.eye_state.get('running') and st.session_state.eye_state.get('fixed_duration'):
            duration = st.session_state.eye_state['fixed_duration'] // 60
            source = "session"
        else:
            duration, source = planned_mins, duration_source

        # Use persisted remaining secs if session was running
        persisted_secs = st.session_state.get('persistent_remaining_secs', 0)
        eye_tracker.embed_eye_tracker(
            initial_mins=duration, 
            state=st.session_state.eye_state, 
            guard_enabled=True, 
            duration_source=source,
            remaining_secs=persisted_secs if persisted_secs > 0 else None
        )



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