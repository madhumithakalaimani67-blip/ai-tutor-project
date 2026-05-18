import streamlit as st
from utils import storage

import datetime

def main(user_id, existing_profile=None, is_setup=True):
    if is_setup:
        st.title("🌟 Welcome to EDUAI")
        st.write("Let's get to know you so we can personalize your experience.")
    else:
        st.markdown("### 📝 Edit Profile Preferences")

    p = existing_profile or {}

    with st.form("onboarding_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("What should we call you?", value=p.get("name", ""), placeholder="e.g. Madhu")
            age_options = ["Under 18", "18-22", "23-30", "30+"]
            age_idx = age_options.index(p.get("age")) if p.get("age") in age_options else 0
            age = st.selectbox("Age Group", age_options, index=age_idx)
            
            status_options = ["High School Student", "College Student", "Working Professional", "Freelancer", "Job Seeker"]
            status_idx = status_options.index(p.get("status")) if p.get("status") in status_options else 0
            status = st.selectbox("Current Status", status_options, index=status_idx)
            
            pace_options = ["Relaxed & Detailed", "Standard Structured", "Fast-Paced Bootcamp"]
            pace_idx = pace_options.index(p.get("pace")) if p.get("pace") in pace_options else 0
            pace = st.selectbox("Preferred Learning Pace", pace_options, index=pace_idx)
            
            primary_goal = st.text_area("What is your specific learning goal?", value=p.get("primary_goal", ""), placeholder="e.g. Master React in 3 months")
            target_deadline = st.text_input("What is your target deadline or timeline? (Optional)", value=p.get("target_deadline", ""), placeholder="e.g. Job ready in 3 months, Exam in June")
            
            reason_options = ["Getting a Job", "Career Switch", "College/University", "Freelancing", "Personal Interest", "Building a Product"]
            r_val = p.get("learning_reason", "")
            reason_idx = reason_options.index(r_val) if r_val in reason_options else 0
            learning_reason = st.selectbox("Why are you learning this? (Optional)", reason_options, index=reason_idx)
            
        with col2:
            skill_options = ["Absolute Beginner", "Familiar / Hobbyist", "Intermediate", "Advanced / Professional"]
            skill_idx = skill_options.index(p.get("skill_level")) if p.get("skill_level") in skill_options else 0
            skill_level = st.selectbox("What is your current skill level in this field?", skill_options, index=skill_idx)
            
            style_options = ["Watching Videos", "Reading Docs", "Coding Projects", "Interactive Quizzes", "Audio / Podcasts"]
            def_style = [s.strip() for s in p.get("learning_style", "").split(",")] if p.get("learning_style") else []
            def_style = [s for s in def_style if s in style_options]
            learning_style = st.multiselect("How do you learn best? (Select multiple)", style_options, default=def_style)
            
            chal_options = ["Procrastination", "Time Management", "Lack of Guidance", "Staying Motivated", "Finding Good Resources"]
            def_chal = [c.strip() for c in p.get("challenges", "").split(",")] if p.get("challenges") else []
            def_chal = [c for c in def_chal if c in chal_options]
            challenges = st.multiselect("What are your biggest learning challenges?", chal_options, default=def_chal)
            
            time_options = ["30 mins", "1 hour", "2 hours", "3+ hours"]
            time_idx = time_options.index(p.get("daily_time")) if p.get("daily_time") in time_options else 0
            daily_time = st.selectbox("How much time can you study daily?", time_options, index=time_idx)
            
            cert_options = ["None", "AWS Certification", "Google Cloud", "GATE", "IELTS", "Company Placement Prep", "Other"]
            cert_val = p.get("target_certification", "None")
            cert_val = cert_val if cert_val else "None"
            cert_idx = cert_options.index(cert_val) if cert_val in cert_options else 0
            target_certification = st.selectbox("What is your target certification or exam? (Optional)", cert_options, index=cert_idx)
            
            preferred_language = st.text_input("Which programming language do you prefer? (Optional)", value=p.get("preferred_language", ""), placeholder="e.g. Python, JavaScript, Java")
            
            device_options = ["Laptop", "Mobile", "Tablet", "Both Laptop and Mobile"]
            d_val = p.get("study_device", "")
            d_val = d_val if d_val in device_options else "Laptop"
            device_idx = device_options.index(d_val) if d_val in device_options else 0
            study_device = st.selectbox("What device do you mostly study on? (Optional)", device_options, index=device_idx)
            
            college_company = st.text_input("Your college or company name? (Optional)", value=p.get("college_company", ""), placeholder="e.g. Anna University, TCS, Infosys")
            
            try:
                rh, rm = map(int, p.get("reminder_time", "20:00").split(":"))
                def_time = datetime.time(rh, rm)
            except:
                def_time = datetime.time(20, 0)
            reminder_time = st.time_input("Reminder Mail Time (Daily)", def_time)

        btn_text = "🚀 Let's Begin" if is_setup else "💾 Update Profile"
        submitted = st.form_submit_button(btn_text)

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
                    "target_deadline": target_deadline if target_deadline else "",
                    "learning_reason": learning_reason if learning_reason else "",
                    "target_certification": target_certification if target_certification else "",
                    "preferred_language": preferred_language if preferred_language else "",
                    "study_device": study_device if study_device else "",
                    "college_company": college_company if college_company else "",
                    "reminder_time": reminder_time.strftime("%H:%M")
                }
                
                if "theme" in p:
                    profile_data["theme"] = p["theme"]
                    
                storage.save_profile(user_id, profile_data)
                st.session_state.user_profile = profile_data
                
                if is_setup:
                    st.session_state.page = "Dashboard"
                    st.success("You're all set! Loading your dashboard...")
                    st.rerun()
                else:
                    st.success("Profile Updated Successfully!")
                    st.rerun()

if __name__ == "__main__":
    main(None)
