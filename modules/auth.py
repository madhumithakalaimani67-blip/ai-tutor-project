import streamlit as st
from utils import storage, email_helper

import base64
import os

def main():
    # Premium Auth CSS
    st.markdown("""
    <style>
        .auth-left-content { 
            padding: 40px; 
            animation: fadeInLeft 0.8s ease-out;
        }
        .auth-feature-card {
            background: rgba(15, 23, 42, 0.45);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        .auth-feature-card:hover {
            transform: translateY(-5px);
            background: rgba(15, 23, 42, 0.6);
            border-color: var(--primary);
        }

        [data-testid="stForm"] {
            width: 100%;
            max-width: 420px;
            margin: 20px auto;
            padding: 30px;
            background: rgba(15, 23, 42, 0.55) !important;
            backdrop-filter: blur(25px);
            border-radius: 25px;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            animation: fadeInRight 0.8s ease-out;
        }
        .auth-title-large { 
            font-size: 4rem !important; font-weight: 800 !important; 
            margin-bottom: 5px;
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        @keyframes fadeInLeft { from { opacity: 0; transform: translateX(-30px); } to { opacity: 1; transform: translateX(0); } }
        @keyframes fadeInRight { from { opacity: 0; transform: translateX(30px); } to { opacity: 1; transform: translateX(0); } }
        @keyframes fadeInDown { from { opacity: 0; transform: translateY(-30px); } to { opacity: 1; transform: translateY(0); } }
        .stButton>button { width: 100%; height: 45px; border-radius: 12px !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    if "reset_email" not in st.session_state:
        st.session_state.reset_email = None

    # Redirect to registration/reset screens if needed
    if st.session_state.get("verifying_email"):
        show_verification_screen()
        return
    
    if st.session_state.auth_mode == "reset":
        show_reset_password_screen()
        return

    st.markdown("""
<div style="text-align: center; margin-top: 10px; margin-bottom: 50px; animation: fadeInDown 0.8s ease-out;">
<h1 class="auth-title-large">EDUAI</h1>
<p style="font-size: 1.5rem; color: white; opacity: 0.9; margin: 0;">
Your Premium AI-Powered <span style="color: #a855f7; font-weight: 700;">Study Companion</span>
</p>
</div>
""", unsafe_allow_html=True)

    # Two Column Layout
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("""
<div style="animation: fadeInLeft 0.8s ease-out; margin-top: 20px;">

<div class="auth-feature-card">
<div style="display: flex; align-items: flex-start;">
<div style="background: rgba(99, 102, 241, 0.15); min-width: 50px; height: 50px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; margin-right: 20px; border: 1px solid rgba(99, 102, 241, 0.4); box-shadow: 0 4px 15px rgba(99, 102, 241, 0.2);">
🛣️
</div>
<div>
<h4 style="margin:0 0 5px 0; color: #6366f1; font-size: 1.25rem; font-weight: 700; letter-spacing: 0.5px;">Smart Roadmaps</h4>
<p style="margin:0; font-size: 0.95rem; opacity: 0.8; line-height: 1.5; color: #f8fafc;">AI-generated learning paths tailored to your domain and time constraints.</p>
</div>
</div>
</div>

<div class="auth-feature-card">
<div style="display: flex; align-items: flex-start;">
<div style="background: rgba(168, 85, 247, 0.15); min-width: 50px; height: 50px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; margin-right: 20px; border: 1px solid rgba(168, 85, 247, 0.4); box-shadow: 0 4px 15px rgba(168, 85, 247, 0.2);">
💬
</div>
<div>
<h4 style="margin:0 0 5px 0; color: #a855f7; font-size: 1.25rem; font-weight: 700; letter-spacing: 0.5px;">24/7 Doubt Solver</h4>
<p style="margin:0; font-size: 0.95rem; opacity: 0.8; line-height: 1.5; color: #f8fafc;">Get instant answers and conceptual clarity for any complex topic.</p>
</div>
</div>
</div>

<div class="auth-feature-card">
<div style="display: flex; align-items: flex-start;">
<div style="background: rgba(14, 165, 233, 0.15); min-width: 50px; height: 50px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; margin-right: 20px; border: 1px solid rgba(14, 165, 233, 0.4); box-shadow: 0 4px 15px rgba(14, 165, 233, 0.2);">
🎯
</div>
<div>
<h4 style="margin:0 0 5px 0; color: #0ea5e9; font-size: 1.25rem; font-weight: 700; letter-spacing: 0.5px;">Focus Tracker</h4>
<p style="margin:0; font-size: 0.95rem; opacity: 0.8; line-height: 1.5; color: #f8fafc;">Monitor your attention and optimize your study sessions with AI.</p>
</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

    with col2:
        # Wrap everything in a single container for the right column
        with st.container():
            
            if st.session_state.auth_mode == "login":
                with st.form("login_form"):
                    st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'><span style='-webkit-text-fill-color: initial;'>🌟</span> Welcome Back</h3>", unsafe_allow_html=True)
                    email = st.text_input("Email", placeholder="yourname@gmail.com")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    
                    # Instagram-style small link below password
                    if st.form_submit_button("Forgot Password?", type="secondary", use_container_width=False):
                        st.session_state.auth_mode = "reset"
                        st.rerun()

                    col_b1, col_b2, col_b3 = st.columns([1, 4, 1])
                    with col_b2:
                        login_submit = st.form_submit_button("🚀 ENTER DASHBOARD", use_container_width=True)

                    if login_submit:
                        user_id = storage.verify_user(email, password)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.session_state.authenticated = True
                            st.rerun()
                        else:
                            st.error("Invalid credentials.")

                col_btn_1, col_btn_2, col_btn_3 = st.columns([1, 4, 1])
                with col_btn_2:
                    if st.button("✨ New User? Create Account", use_container_width=True):
                        st.session_state.auth_mode = "signup"
                        st.rerun()

            elif st.session_state.auth_mode == "signup":
                with st.form("signup_form"):
                    st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'><span style='-webkit-text-fill-color: initial;'>✨</span> Create Account</h3>", unsafe_allow_html=True)
                    new_email = st.text_input("New Email", placeholder="yourname@gmail.com")
                    new_pass = st.text_input("Password", type="password", placeholder="Min 6 chars")
                    confirm_pass = st.text_input("Confirm", type="password")
                    
                    col_b1, col_b2, col_b3 = st.columns([1, 4, 1])
                    with col_b2:
                        signup_submit = st.form_submit_button("🎯 GET ACCESS CODE", use_container_width=True)

                    if signup_submit:
                        if storage.email_exists(new_email):
                            st.warning("⚠️ This email is already registered. Please Login.")
                            st.session_state.auth_mode = "login"
                        elif new_pass != confirm_pass or len(new_pass) < 6:
                            st.error("Invalid password entry.")
                        else:
                            otp = email_helper.generate_otp()
                            if email_helper.send_otp_email(new_email, otp):
                                storage.save_pending_user(new_email, new_pass, otp)
                                st.session_state.verifying_email = new_email
                                st.session_state.pending_pass = new_pass
                                st.rerun()

                col_btn_1, col_btn_2, col_btn_3 = st.columns([1, 4, 1])
                with col_btn_2:
                    if st.button("⬅ Back to Login", use_container_width=True):
                        st.session_state.auth_mode = "login"
                        st.rerun()

def show_verification_screen():
    with st.container():
        
        with st.form("verify_form"):
            st.markdown(f"### 🛡️ Verify Email\nCode sent to: **{st.session_state.verifying_email}**")
            
            code = st.text_input("6-digit Code", placeholder="XXXXXX")
            submit = st.form_submit_button("VALIDATE & JOIN")
            
            if submit:
                user_id = storage.verify_otp(st.session_state.verifying_email, code)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.authenticated = True
                    st.session_state.verifying_email = None
                    st.rerun()
                else:
                    st.error("Invalid code.")
        
        if st.button("⬅ Cancel"):
            st.session_state.verifying_email = None
            st.rerun()

def show_reset_password_screen():
    with st.container():
        
        if not st.session_state.get("reset_step"):
            st.session_state.reset_step = 1

        if st.session_state.reset_step == 1:
            with st.form("forgot_form"):
                st.markdown("### 🔑 Reset Password")
                email = st.text_input("Enter Registered Email")
                submit = st.form_submit_button("SEND RESET CODE")
                if submit:
                    if storage.email_exists(email):
                        otp = email_helper.generate_otp()
                        if email_helper.send_otp_email(email, otp):
                            st.session_state.reset_email = email
                            st.session_state.reset_otp = otp
                            st.session_state.reset_step = 2
                            st.rerun()
                    else:
                        st.error("Email not found.")
        
        elif st.session_state.reset_step == 2:
            with st.form("reset_verify"):
                st.markdown("### 🔑 Reset Password")
                code = st.text_input("Enter Reset Code")
                new_pass = st.text_input("New Password", type="password")
                submit = st.form_submit_button("UPDATE PASSWORD")
                if submit:
                    if code == st.session_state.reset_otp:
                        storage.reset_password(st.session_state.reset_email, new_pass)
                        st.success("Password Updated!")
                        st.session_state.auth_mode = "login"
                        st.session_state.reset_step = 1
                        st.rerun()
                    else:
                        st.error("Invalid Code.")

        if st.button("⬅ Back"):
            st.session_state.auth_mode = "login"
            st.session_state.reset_step = 1
            st.rerun()

if __name__ == "__main__":
    main()