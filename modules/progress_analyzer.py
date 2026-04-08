import streamlit as st
import pandas as pd
import altair as alt
from utils import storage, ai_helper

def main(user_id):
    st.title("📈 Performance Insights")
    st.write("Deep dive into your focus and consistency metrics.")

    sessions = storage.get_sessions(user_id)
    if not sessions:
        st.info("No study sessions yet. Start one to see your progress!")
        return

    # Data Prep
    df = pd.DataFrame(sessions)
    df['Date'] = pd.to_datetime(df['start_time']).dt.date
    
    # Aggregates
    total_time = df['actual_duration'].sum()
    avg_focus = int(df['focus_score'].mean())
    streak = storage.get_streak(user_id)
    total_pauses = df['pause_count'].sum()

    # Premium Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🔥 Streak", f"{streak} Days")
    with c2:
        st.metric("⏱ Total Studied", f"{total_time} mins")
    with c3:
        st.metric("🎯 Avg Focus", f"{avg_focus}%")
    with c4:
        st.metric("⏸ Total Pauses", f"{total_pauses}")

    st.markdown("---")

    # Altair Chart: Focus Over Time (Area Chart)
    st.markdown("### 📊 Focus Score Trend")
    focus_chart = alt.Chart(df).mark_area(
        line={'color': '#6366f1'},
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='#6366f1', offset=0),
                   alt.GradientStop(color='transparent', offset=1)],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x=alt.X('start_time:T', title='Timeline'),
        y=alt.Y('focus_score:Q', title='Focus Score (%)', scale=alt.Scale(domain=[0, 100])),
        tooltip=['start_time:T', 'focus_score:Q', 'actual_duration:Q']
    ).properties(height=300).interactive()
    
    st.altair_chart(focus_chart, use_container_width=True)

    # Altair Chart: Duration vs pauses (Grouped Bar Chart)
    st.markdown("### ⏱ Session Duration & Pauses")
    bar_df = df.copy()
    bar_df = bar_df.melt(id_vars='start_time', value_vars=['actual_duration', 'pause_count'],
                          var_name='Metric', value_name='Value')
    
    bar_chart = alt.Chart(bar_df).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
        x=alt.X('start_time:T', title='Timeline'),
        y=alt.Y('Value:Q', title='Count / Minutes'),
        color=alt.Color('Metric:N', scale=alt.Scale(range=['#a855f7', '#6366f1'])),
        tooltip=['start_time:T', 'Metric:N', 'Value:Q']
    ).properties(height=350).interactive()

    st.altair_chart(bar_chart, use_container_width=True)

    # Session Logs
    with st.expander("📝 Detailed Session Logs"):
        if not df.empty:
            for _, s in df.iterrows():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                with c1: st.write(f"📅 {str(s['start_time'])[:16]}")
                with c2: st.write(f"⏱ {s['actual_duration']} min")
                with c3: st.write(f"🎯 {s['focus_score']}%")
                with c4: 
                    if st.button("🗑️", key=f"prog_del_{s['id']}"):
                        storage.delete_session(s['id'])
                        st.rerun()
        else:
            st.info("No logs available.")

    if st.button("🧠 Get AI Growth Tips"):
        agent = ai_helper.get_ai_agent()
        with st.spinner("Analyzing your focus patterns..."):
            prompt = f"Analyze these stats concisely: {total_time} total mins, {avg_focus}% avg focus, {total_pauses} pauses, and {streak} days streak. Suggest 3 ways to improve."
            ans = agent.chat([{"role": "user", "content": prompt}], user_profile=st.session_state.get('user_profile'))
            if ans:
                st.markdown(ans.choices[0].message.content)

def show_summary(user_id):
    """Lite summary for dashboard."""
    sessions = storage.get_sessions(user_id)
    if sessions:
        total = sum([s['actual_duration'] for s in sessions])
        st.write(f"📊 **{total} mins** focused across {len(sessions)} sessions.")
