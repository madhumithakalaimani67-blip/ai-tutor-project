import streamlit as st
from utils import storage

def main(user_id):
    st.title("🌟 Welcome to EDUAI")
    st.write("Let's get to know you so we can personalize your experience.")

    with st.form("onboarding_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("What should we call you?", placeholder="e.g. Madhu")
            age = st.selectbox("Age Group", ["Under 18", "18-22", "23-30", "30+"])
            status = st.selectbox("Current Status", ["High School Student", "College Student", "Working Professional", "Freelancer", "Job Seeker"])
            pace = st.selectbox("Preferred Learning Pace", ["Relaxed & Detailed", "Standard Structured", "Fast-Paced Bootcamp"])
            primary_goal = st.text_area("What is your specific learning goal?", placeholder="e.g. Master React in 3 months")
            known_topics = st.text_input("What topics do you already know in this field? (Optional)", placeholder="e.g. I know basic Python, HTML basics")
            target_deadline = st.text_input("What is your target deadline or timeline? (Optional)", placeholder="e.g. Job ready in 3 months, Exam in June")
            learning_reason = st.selectbox("Why are you learning this? (Optional)", ["Getting a Job", "Career Switch", "College/University", "Freelancing", "Personal Interest", "Building a Product"])
            
        with col2:
            skill_level = st.selectbox("What is your current skill level in this field?", 
                ["Absolute Beginner", "Familiar / Hobbyist", "Intermediate", "Advanced / Professional"])
            learning_style = st.multiselect("How do you learn best? (Select multiple)", 
                ["Watching Videos", "Reading Docs", "Coding Projects", "Interactive Quizzes", "Audio / Podcasts"])
            challenges = st.multiselect("What are your biggest learning challenges?", 
                ["Procrastination", "Time Management", "Lack of Guidance", "Staying Motivated", "Finding Good Resources"])
            daily_time = st.selectbox("How much time can you study daily?", ["30 mins", "1 hour", "2 hours", "3+ hours"])
            target_certification = st.selectbox("What is your target certification or exam? (Optional)", ["None", "AWS Certification", "Google Cloud", "GATE", "IELTS", "Company Placement Prep", "Other"])
            preferred_language = st.text_input("Which programming language do you prefer? (Optional)", placeholder="e.g. Python, JavaScript, Java")
            study_device = st.selectbox("What device do you mostly study on? (Optional)", ["Laptop", "Mobile", "Tablet", "Both Laptop and Mobile"])
            college_company = st.text_input("Your college or company name? (Optional)", placeholder="e.g. Anna University, TCS, Infosys")
            
            import datetime
            reminder_time = st.time_input("Reminder Mail Time (Daily)", datetime.time(20, 0))

        submitted = st.form_submit_button("🚀 Let's Begin")

        if submitted:
            if not name:
                st.error("Name is required to personalize your experience.")
            else:
                profile_data = {
                    "name": name,
                    "age": age,
                    "status": status,
                    "pace": pace,
                    "skill_level": skill_level,
                    "learning_style": ", ".join(learning_style) if learning_style else "Mixed",
                    "challenges": ", ".join(challenges) if challenges else "None",
                    "daily_time": daily_time,
                    "primary_goal": primary_goal,
                    "known_topics": known_topics if known_topics else "",
                    "target_deadline": target_deadline if target_deadline else "",
                    "learning_reason": learning_reason if learning_reason else "",
                    "target_certification": target_certification if target_certification else "",
                    "preferred_language": preferred_language if preferred_language else "",
                    "study_device": study_device if study_device else "",
                    "college_company": college_company if college_company else "",
                    "reminder_time": reminder_time.strftime("%H:%M")
                }
                storage.save_profile(user_id, profile_data)
                st.session_state.user_profile = profile_data
                st.session_state.page = "Dashboard"
                st.success("You're all set! Loading your dashboard...")
                st.rerun()

if __name__ == "__main__":
    main(None)
