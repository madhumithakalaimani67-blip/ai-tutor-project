import streamlit as st
import pandas as pd
import altair as alt
from utils import storage, ai_helper

def main(user_id):
    st.markdown("<h1 style='text-align:center;'>📈 Performance Mission Debrief</h1>", unsafe_allow_html=True)
    
    sessions = storage.get_sessions(user_id)
    if not sessions:
        st.markdown("""
        <div class="eduai-mission-card" style="text-align:center;">
            <h3>No data in the vault 🛰️</h3>
            <p>Start your first mission in the Focus Hub to see your telemetry here.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Data Prep
    df = pd.DataFrame(sessions)
    df['Date'] = pd.to_datetime(df['start_time'], format='ISO8601', errors='coerce').dt.date
    
    # Aggregates
    total_time = df['actual_duration'].sum()
    avg_focus = int(df['focus_score'].mean())
    streak = storage.get_streak(user_id)
    total_dist = df['distraction_count'].sum() if 'distraction_count' in df else 0
    
    # Metrics Section (Fixed Size Dashboard)
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("☄️ Total Flight Time", f"{total_time} mins")
    with c2:
        st.metric("🔥 Streak", f"{streak} Days")
    with c3:
        st.metric("🛡️ Focus Interrupted", f"{total_dist} times")

    st.markdown("---")

    # ── CIRCULAR CHARTS SECTION ──
    st.markdown("### 📊 Core Analytics")
    col1, col2, col3 = st.columns(3)

    # 1. Focus Score Circle
    with col1:
        st.markdown("<div align='center'><b>AVG FOCUS</b></div>", unsafe_allow_html=True)
        focus_data = pd.DataFrame({"Category": ["Focused", "Distracted"], "Value": [avg_focus, 100-avg_focus]})
        donut_focus = alt.Chart(focus_data).mark_arc(innerRadius=50, cornerRadius=10).encode(
            theta=alt.Theta(field="Value", type="quantitative"),
            color=alt.Color(field="Category", type="nominal", scale=alt.Scale(range=["#6366f1", "rgba(255,255,255,0.1)"])),
            tooltip=["Category", "Value"]
        ).properties(width=200, height=200)
        st.altair_chart(donut_focus, use_container_width=True)

    # 2. Task Completion Circle
    with col2:
        st.markdown("<div align='center'><b>TASK COMPLETION</b></div>", unsafe_allow_html=True)
        latest_rm = storage.get_latest_roadmap(user_id)
        if latest_rm:
            tasks = storage.get_tasks(user_id, latest_rm['id'])
            done = len([t for t in tasks if t['status'] == 'done'])
            pending = len([t for t in tasks if t['status'] == 'pending'])
            if tasks:
                task_data = pd.DataFrame({"Status": ["Done", "Pending"], "Count": [done, pending]})
                donut_tasks = alt.Chart(task_data).mark_arc(innerRadius=50, cornerRadius=10).encode(
                    theta=alt.Theta(field="Count", type="quantitative"),
                    color=alt.Color(field="Status", type="nominal", scale=alt.Scale(range=["#10b981", "rgba(255,255,255,0.1)"])),
                    tooltip=["Status", "Count"]
                ).properties(width=200, height=200)
                st.altair_chart(donut_tasks, use_container_width=True)
            else: st.caption("No tasks allocated.")
        else: st.caption("No roadmap found.")

    # 3. Distraction Breakdown Circle
    with col3:
        st.markdown("<div align='center'><b>DISTRACTION TYPE</b></div>", unsafe_allow_html=True)
        d_types = {
            "Phone": df['phone_count'].sum() if 'phone_count' in df else 0,
            "Drowsy": df['drowsy_count'].sum() if 'drowsy_count' in df else 0,
            "Zone-out": df['zone_out_count'].sum() if 'zone_out_count' in df else 0
        }
        if sum(d_types.values()) > 0:
            dist_df = pd.DataFrame([{"Type": k, "Count": v} for k, v in d_types.items()])
            donut_dist = alt.Chart(dist_df).mark_arc(innerRadius=50, cornerRadius=10).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Type", type="nominal", scale=alt.Scale(range=["#f59e0b", "#ef4444", "#a855f7"])),
                tooltip=["Type", "Count"]
            ).properties(width=200, height=200)
            st.altair_chart(donut_dist, use_container_width=True)
        else:
            st.caption("Perfect Discipline! No distractions.")

    st.markdown("---")
    
    # ── LOGS & AI ──
    c_log, c_ai = st.columns([1, 1])
    with c_log:
        st.markdown("### 📝 Mission Logs")
        for _, s in df.iloc[::-1].iterrows():
            with st.expander(f"📅 {str(s['start_time'])[:16]}", expanded=False):
                st.write(f"⏱ **Duration:** {s['actual_duration']} min")
                st.write(f"🎯 **Score:** {s['focus_score']}%")
                if 'distraction_count' in s: st.write(f"🛡️ **Distractions:** {s['distraction_count']}")
                if st.button("Delete Session", key=f"del_sess_{s['id']}"):
                    storage.delete_session(s['id'])
                    st.rerun()

    with c_ai:
        st.markdown("### 🧠 AI Growth Tactics")
        if st.button("Generate Tactical Briefing", use_container_width=True):
            agent = ai_helper.get_ai_agent()
            with st.spinner("Decoding patterns..."):
                prompt = f"Analyze: {total_time} mins, {avg_focus}% focus, {total_dist} distractions. Suggest 3 behavioral shifts for peak performance."
                ans = agent.chat([{"role": "user", "content": prompt}], user_profile=st.session_state.get('user_profile'))
                if ans:
                    st.info(ans.choices[0].message.content)

def show_summary(user_id):
    """Lite summary for dashboard."""
    sessions = storage.get_sessions(user_id)
    if sessions:
        total = sum([s['actual_duration'] for s in sessions])
        st.write(f"📊 **{total} mins** focused. Excellent work.")
