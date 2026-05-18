import streamlit as st
import pandas as pd
import altair as alt
from utils import storage, ai_helper, excel_generator, pdf_generator
from datetime import datetime

def main(user_id):
    st.markdown("""
    <style>
        .prog-title { font-size: 2.2rem !important; font-weight: 800 !important; color: #e2e8f0; margin: 0; }
        .prog-subtitle { color: #94a3b8; font-size: 0.95rem; margin-top: 3px; margin-bottom: 20px; }

        /* Roadmap Selector Card */
        .rm-selector {
            background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.25);
            border-radius: 12px; padding: 14px 20px; margin-bottom: 24px;
            display: flex; align-items: center; gap: 12px;
        }
        .rm-label { font-size: 0.75rem; color: #94a3b8; font-weight: 700;
                    text-transform: uppercase; letter-spacing: 1px; white-space: nowrap; }

        .kpi-grid { display: flex; gap: 15px; margin-bottom: 28px; }
        .kpi-card {
            flex: 1; background: rgba(30,41,59,0.7);
            border-left: 4px solid #6366f1; border-radius: 8px;
            padding: 14px 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .kpi-val { font-size: 1.7rem; font-weight: 800; color: white;
                   margin: 5px 0 0 0; line-height: 1.2; font-family: 'Courier New', monospace; }
        .kpi-lbl { font-size: 0.72rem; color: #cbd5e1; text-transform: uppercase;
                   font-weight: 700; letter-spacing: 1px; margin: 0; }

        .panel { background: rgba(15,23,42,0.5); border: 1px solid rgba(255,255,255,0.05);
                 border-radius: 12px; padding: 20px; margin-bottom: 20px; }
        .panel-title { font-size: 1.05rem; font-weight: 700; color: #f8fafc; margin-bottom: 15px;
                       border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px; }
        .ai-box { background: rgba(168,85,247,0.1); border: 1px solid rgba(168,85,247,0.3);
                  border-radius: 12px; padding: 18px; margin-bottom: 20px; }
        .ai-title { color: #c084fc; font-weight: 800; margin-bottom: 10px; font-size: 1rem; }
        .traj-tag { font-size: 0.7rem; color: #64748b; text-transform: uppercase;
                    letter-spacing: 1px; font-weight: 700; margin-bottom: 5px; }

        /* Premium Download Button Styling */
        div[data-testid="stDownloadButton"] button {
            background: rgba(99, 102, 241, 0.15) !important;
            border: 1px solid rgba(99, 102, 241, 0.4) !important;
            color: #cbd5e1 !important;
            border-radius: 8px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            height: 38px !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stDownloadButton"] button:hover {
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
            border: 1px solid transparent !important;
            color: white !important;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
            transform: translateY(-2px) !important;
        }
        div[data-testid="stDownloadButton"] button:active {
            transform: translateY(0px) !important;
        }
    </style>
    <h1 class="prog-title">ANALYTICS WORKSPACE</h1>
    <div class="prog-subtitle">Session Telemetry & Performance Logs</div>
    """, unsafe_allow_html=True)

    # ── ROADMAP SELECTOR ──────────────────────────────────────────────────────
    all_roadmaps = storage.get_all_roadmaps(user_id) or []
    rm_options = {"🌐 All Roadmaps (Combined)": None}
    for rm in all_roadmaps:
        label = f"📌 {rm['goal'][:55]}{'...' if len(rm['goal']) > 55 else ''}"
        rm_options[label] = rm['id']

    st.markdown("<div style='margin-bottom:6px; font-size:0.75rem; color:#94a3b8; text-transform:uppercase; font-weight:700; letter-spacing:1px;'>📂 Viewing Analytics For</div>", unsafe_allow_html=True)
    selected_label = st.selectbox(
        label="roadmap_select", label_visibility="collapsed",
        options=list(rm_options.keys()),
        key="prog_rm_selector"
    )
    selected_rm_id = rm_options[selected_label]
    selected_rm = next((r for r in all_roadmaps if r['id'] == selected_rm_id), None) if selected_rm_id else None

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ── DATA LOAD (filtered or all) ───────────────────────────────────────────
    if selected_rm_id:
        sessions = storage.get_sessions_by_roadmap(user_id, selected_rm_id)
    else:
        sessions = storage.get_sessions(user_id)

    if not sessions:
        st.info("No session data for this roadmap yet. Start a focus session to generate telemetry!")
        return

    df = pd.DataFrame(sessions)
    df['Date'] = pd.to_datetime(df['start_time'], errors='coerce')
    df = df.dropna(subset=['Date'])

    df['focus_score']      = pd.to_numeric(df['focus_score'], errors='coerce')
    df['actual_duration']  = pd.to_numeric(df['actual_duration'], errors='coerce')
    df['distraction_count']= pd.to_numeric(df.get('distraction_count', 0), errors='coerce')

    total_time  = df['actual_duration'].sum()
    avg_focus   = int(df['focus_score'].mean()) if not pd.isna(df['focus_score'].mean()) else 0
    streak      = storage.get_streak(user_id)
    total_dist  = int(df['distraction_count'].sum())

    # ── KPI GRID ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card" style="border-color: #38bdf8;">
            <p class="kpi-lbl">Flight Time</p>
            <h2 class="kpi-val">{int(total_time//60)}h {int(total_time%60)}m</h2>
        </div>
        <div class="kpi-card" style="border-color: #10b981;">
            <p class="kpi-lbl">Avg Focus</p>
            <h2 class="kpi-val">{avg_focus}%</h2>
        </div>
        <div class="kpi-card" style="border-color: #f43f5e;">
            <p class="kpi-lbl">Active Streak</p>
            <h2 class="kpi-val">{streak} Days</h2>
        </div>
        <div class="kpi-card" style="border-color: #a855f7;">
            <p class="kpi-lbl">Distractions</p>
            <h2 class="kpi-val">{total_dist}</h2>
        </div>
        <div class="kpi-card" style="border-color: #f59e0b;">
            <p class="kpi-lbl">Sessions</p>
            <h2 class="kpi-val">{len(df)}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 2-COLUMN LAYOUT ───────────────────────────────────────────────────────
    col_main, col_side = st.columns([2.5, 1])

    with col_main:
        # ── TRAJECTORY ────────────────────────────────────────────────────────
        st.markdown("<div class='panel'><div class='panel-title'>📈 Performance Trajectory</div>", unsafe_allow_html=True)
        if len(df) >= 1:
            num_days = df['Date'].dt.date.nunique()

            # Smart grouping: daily → weekly → monthly
            if num_days <= 7:
                # Daily: one dot per day
                trend_df = df.groupby(df['Date'].dt.date)['focus_score'].mean().reset_index()
                trend_df.columns = ['Period', 'Score']
                trend_df['Period'] = pd.to_datetime(trend_df['Period'])
                x_fmt, x_title = "%b %d", "Daily"
            elif num_days <= 30:
                # Weekly: one dot per week
                df['Week'] = df['Date'].dt.to_period('W').dt.start_time
                trend_df = df.groupby('Week')['focus_score'].mean().reset_index()
                trend_df.columns = ['Period', 'Score']
                x_fmt, x_title = "Week of %b %d", "Weekly"
            else:
                # Monthly: one dot per month
                df['Month'] = df['Date'].dt.to_period('M').dt.start_time
                trend_df = df.groupby('Month')['focus_score'].mean().reset_index()
                trend_df.columns = ['Period', 'Score']
                x_fmt, x_title = "%b %Y", "Monthly"

            trend_df['Score'] = trend_df['Score'].round(1)
            st.markdown(f"<div class='traj-tag'>Grouping: {x_title} averages · {len(trend_df)} data points</div>", unsafe_allow_html=True)

            base = alt.Chart(trend_df).encode(
                x=alt.X('Period:T', title='', axis=alt.Axis(
                    grid=True, gridColor='rgba(255,255,255,0.05)',
                    labelColor='#94a3b8', format=x_fmt, tickColor='transparent'
                )),
                y=alt.Y('Score:Q', title='Avg Focus %', scale=alt.Scale(domain=[0, 100]),
                    axis=alt.Axis(gridColor='rgba(255,255,255,0.06)', labelColor='#94a3b8')),
                tooltip=['Period:T', alt.Tooltip('Score:Q', format='.0f', title='Avg Score')]
            )
            line = base.mark_line(color='#2dd4bf', size=2.5, strokeDash=[6, 4], interpolate='monotone')
            dots = base.mark_point(color='#2dd4bf', filled=True, size=80, opacity=1)
            chart = (line + dots).properties(height=260, background='transparent').interactive(bind_x=False, bind_y=False)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("Complete a session to plot the trajectory.")
        st.markdown("</div>", unsafe_allow_html=True)

        # ── MISSION VAULT ──────────────────────────────────────────────────────
        st.markdown("<div class='panel'><div class='panel-title'>🗄️ Mission Vault</div>", unsafe_allow_html=True)

        render_session_history(user_id, sessions)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_side:
        # ── AI TACTICS ──
        st.markdown("""
        <div class="ai-box">
            <div class="ai-title">🤖 AI Insights</div>
        """, unsafe_allow_html=True)
        if st.button("Generate Briefing", use_container_width=True, type="primary"):
            agent = ai_helper.get_ai_agent()
            with st.spinner("Analyzing..."):
                prompt = f"Analyze: {total_time} mins, {avg_focus}% avg focus, {total_dist} total distractions. Suggest 2 highly specific behavioral shifts for peak performance in a brief, professional data-analyst tone."
                ans = agent.chat([{"role": "user", "content": prompt}], user_profile=st.session_state.get('user_profile'))
                if ans:
                    st.markdown(f"<div style='margin-top:15px; color:#e2e8f0; font-size:0.85rem; line-height:1.5;'>{ans.choices[0].message.content}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── REPORT EXPORT CENTER ──
        st.markdown("""
        <div class="panel">
            <div class="panel-title">📥 Report Export Center</div>
            <div style="font-size:0.75rem; color:#94a3b8; margin-bottom:12px; line-height:1.4;">
                Download your comprehensive study session reports and distraction analytics in high-fidelity PDF or Excel spreadsheet formats.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Retrieve user profile and generate reports
        user_profile = storage.get_profile(user_id)
        excel_data = excel_generator.generate_excel_report(sessions, selected_label)
        pdf_data = pdf_generator.generate_pdf_report(user_profile, sessions, selected_label)

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            if excel_data:
                st.download_button(
                    label="📊 Excel Sheet",
                    data=excel_data,
                    file_name=f"eduai_focus_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_excel_btn",
                    use_container_width=True
                )
        with dl_col2:
            if pdf_data:
                st.download_button(
                    label="📄 PDF Report",
                    data=pdf_data,
                    file_name=f"eduai_focus_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    key="dl_pdf_btn",
                    use_container_width=True
                )
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # ── CORE ANALYTICS (ONE BY ONE) ──
        st.markdown("<div class='panel'><div class='panel-title'>Core Analytics</div>", unsafe_allow_html=True)
        
        # 1. Focus Distribution
        st.markdown("<div style='text-align:center; font-size:0.8rem; color:#94a3b8; font-weight:700; margin-bottom:-10px;'>FOCUS EFFICIENCY</div>", unsafe_allow_html=True)
        focus_data = pd.DataFrame({"Category": ["Focused", "Distracted"], "Value": [avg_focus, 100-avg_focus]})
        donut_focus = alt.Chart(focus_data).mark_arc(innerRadius=45, cornerRadius=6).encode(
            theta=alt.Theta(field="Value", type="quantitative"),
            color=alt.Color(field="Category", type="nominal", scale=alt.Scale(range=["#6366f1", "rgba(255,255,255,0.1)"]), legend=None),
            tooltip=["Category", "Value"]
        ).properties(height=160, background="transparent")
        st.altair_chart(donut_focus, use_container_width=True)

        st.markdown("<hr style='border-color:rgba(255,255,255,0.05); margin: 10px 0;'>", unsafe_allow_html=True)

        # 2. Distraction Types
        st.markdown("<div style='text-align:center; font-size:0.8rem; color:#94a3b8; font-weight:700; margin-bottom:-10px;'>DISTRACTION MIX</div>", unsafe_allow_html=True)
        d_types = {
            "Phone": df['phone_count'].sum() if 'phone_count' in df else 0,
            "Drowsiness": df['drowsy_count'].sum() if 'drowsy_count' in df else 0,
            "Zone-out": df['zone_out_count'].sum() if 'zone_out_count' in df else 0
        }
        if sum(d_types.values()) > 0:
            dist_df = pd.DataFrame([{"Type": k, "Count": v} for k, v in d_types.items() if v > 0])
            donut_dist = alt.Chart(dist_df).mark_arc(innerRadius=45, cornerRadius=6).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Type", type="nominal", scale=alt.Scale(range=["#f59e0b", "#ef4444", "#a855f7"]), legend=None),
                tooltip=["Type", "Count"]
            ).properties(height=160, background="transparent")
            st.altair_chart(donut_dist, use_container_width=True)
        else:
            st.caption("No distractions logged.")

        st.markdown("<hr style='border-color:rgba(255,255,255,0.05); margin: 10px 0;'>", unsafe_allow_html=True)

        # 3. Task Completion
        st.markdown("<div style='text-align:center; font-size:0.8rem; color:#94a3b8; font-weight:700; margin-bottom:-10px;'>MISSION PROGRESS</div>", unsafe_allow_html=True)
        
        # Pull tasks based on selected dropdown filter
        target_tasks = []
        if selected_rm_id:
            target_tasks = storage.get_tasks(user_id, selected_rm_id) or []
        else:
            # Combined Roadmaps: gather all tasks from all goals
            all_rm = storage.get_all_roadmaps(user_id) or []
            for r in all_rm:
                target_tasks.extend(storage.get_tasks(user_id, r['id']) or [])
        
        if target_tasks:
            total = len(target_tasks)
            done = len([t for t in target_tasks if t['status'] == 'done'])
            pending = total - done
            
            task_data = pd.DataFrame({"Status": ["Done", "Pending"], "Count": [done, pending]})
            # Use premium glassmorphic transparent white (0.15) instead of invisible 0.05 for pending segments
            donut_tasks = alt.Chart(task_data).mark_arc(innerRadius=45, cornerRadius=6).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Status", type="nominal", scale=alt.Scale(range=["#10b981", "rgba(255, 255, 255, 0.15)"]), legend=None),
                tooltip=["Status", "Count"]
            ).properties(height=160, background="transparent")
            st.altair_chart(donut_tasks, use_container_width=True)
        else:
            st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
            st.caption("No tasks logged yet.")
            st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)




def render_session_history(user_id, sessions):
    st.markdown("""
    <style>
    .v-header { display: flex; padding: 10px 15px; border-bottom: 1px solid rgba(255,255,255,0.08); color: #94a3b8; font-weight: 700; text-transform: uppercase; font-size: 0.75rem; }
    .v-row { display: flex; align-items: center; padding: 12px 15px; border-bottom: 1px solid rgba(255,255,255,0.02); transition: background 0.2s; }
    .v-row:hover { background: rgba(255,255,255,0.03); }
    .v-col { flex: 1; color: #e2e8f0; font-size: 0.85rem; }
    .v-score { font-family: 'Courier New', monospace; font-weight: 800; font-size: 0.95rem; }
    .v-stat-val { font-family: 'Courier New', monospace; font-weight: 600; }
    .v-stat-val.zero { opacity: 0.2; }
    </style>
    """, unsafe_allow_html=True)

    c_head1, c_head2 = st.columns([10, 1])
    with c_head1:
        st.markdown("""
        <div class="v-header">
            <div class="v-col" style="flex:2;">Date & Time</div>
            <div class="v-col">Duration</div>
            <div class="v-col">Score</div>
            <div class="v-col">📱 Phone</div>
            <div class="v-col">😴 Drowsy</div>
            <div class="v-col">👁️ Zone</div>
            <div class="v-col">⏸️ Pause</div>
        </div>
        """, unsafe_allow_html=True)

    for s in sessions:
        # Robust Date Parsing
        try:
            dt = pd.to_datetime(s['start_time'])
            d_str = dt.strftime("%b %d, %Y")
            t_str = dt.strftime("%I:%M %p")
        except:
            d_str, t_str = "Unknown Date", "—"

        score = int(s.get('focus_score', 0))
        mins = round(float(s.get('actual_duration', 0)), 1)
        phone = s.get('phone_count', 0)
        drowsy = s.get('drowsy_count', 0)
        zone = s.get('zone_out_count', 0)
        pause = s.get('pause_count', 0)

        if score >= 80: s_col = "#10b981"
        elif score >= 60: s_col = "#f59e0b"
        else: s_col = "#ef4444"

        def f_stat(val): return f"<span class='v-stat-val'>{val}</span>" if val else "<span class='v-stat-val zero'>-</span>"

        c1, c2 = st.columns([10, 1])
        with c1:
            st.markdown(f"""
            <div class="v-row" style="margin-top:-16px;">
                <div class="v-col" style="flex:2;">
                    <div style="font-weight:600;">{d_str}</div>
                    <div style="color:#94a3b8; font-size:0.75rem;">{t_str}</div>
                </div>
                <div class="v-col">{mins}m</div>
                <div class="v-col v-score" style="color: {s_col};">{score}%</div>
                <div class="v-col">{f_stat(phone)}</div>
                <div class="v-col">{f_stat(drowsy)}</div>
                <div class="v-col">{f_stat(zone)}</div>
                <div class="v-col">{f_stat(pause)}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button("🗑️", key=f"del_{s['id']}", help="Delete"):
                storage.delete_session(s['id'])
                st.rerun()


def show_summary(user_id):
    """Lite summary for dashboard."""
    sessions = storage.get_sessions(user_id)
    if sessions:
        total = sum([s['actual_duration'] for s in sessions])
        st.write(f"📊 **{total} mins** focused. Excellent work.")
