import streamlit as st
from utils import storage

def main(user_id):
    st.title("🌟 Welcome to EDUAI")
    st.write("Let's get to know you so we can personalize your experience.")

    with st.form("onboarding_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("What should we call you?", placeholder="e.g. Madhu")
            email = st.text_input("Your Email", placeholder="e.g. Madhu@gmail.com")
            age = st.selectbox("Age Group", ["Under 18", "18-22", "23-30", "30+"])
            primary_goal = st.text_area("What is your primary learning goal?", placeholder="e.g. Master React in 3 months")
            
        with col2:
            interests = st.multiselect("What are you into?", 
                ["AI / Machine Learning", "Web Development", "Data Science", "Competitive Programming", 
                 "Mobile Apps", "Cybersecurity", "Cloud / DevOps", "Design / UI-UX", "Exam Prep", "Other"])
            learning_style = st.radio("How do you learn best?", ["Watching Videos", "Reading Docs", "Coding Projects", "Mixed"])
            daily_time = st.selectbox("How much time can you study daily?", ["30 mins", "1 hour", "2 hours", "3+ hours"])

        submitted = st.form_submit_button("🚀 Let's Begin")

        if submitted:
            if not name or not email:
                st.error("Name and Email are required.")
            else:
                profile_data = {
                    "name": name,
                    "email": email,
                    "age": age,
                    "interests": ", ".join(interests),
                    "learning_style": learning_style,
                    "daily_time": daily_time,
                    "primary_goal": primary_goal
                }
                storage.save_profile(user_id, profile_data)
                st.session_state.user_profile = profile_data
                st.success("You're all set! Head to the Roadmap to set your first goal.")
                st.rerun()

if __name__ == "__main__":
    main(None)
