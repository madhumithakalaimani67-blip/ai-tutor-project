import streamlit as st
from utils import storage, email_helper

import base64
import os

def main():
    st.markdown("""
    <style>
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
        }
        [data-testid="stForm"] {
            width: 100%; max-width: 420px;
            margin: 20px auto; padding: 30px;
            background: rgba(15, 23, 42, 0.55) !important;
            backdrop-filter: blur(25px);
            border-radius: 25px;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            animation: fadeInRight 0.8s ease-out;
        }
        .auth-title-large {
            font-size: 4rem !important; font-weight: 800 !important;
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        @keyframes fadeInLeft  { from{opacity:0;transform:translateX(-30px)}to{opacity:1;transform:translateX(0)} }
        @keyframes fadeInRight { from{opacity:0;transform:translateX( 30px)}to{opacity:1;transform:translateX(0)} }
        @keyframes fadeInDown  { from{opacity:0;transform:translateY(-30px)}to{opacity:1;transform:translateY(0)} }

        /* ============================================================
           BUTTON STYLES — one rule per role, zero conflicts
        ============================================================ */

        /* 🚀 PRIMARY FORM BUTTONS (Enter Dashboard, Send Code, Validate, Update) */
        .stFormSubmitButton > button {
            background: linear-gradient(135deg, #6366f1, #a855f7) !important;
            color: #ffffff !important;
            border: none !important;
            height: 50px !important;
            font-size: 1rem !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            box-shadow: 0 0 22px rgba(99,102,241,0.55) !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
        }
        .stFormSubmitButton > button:hover {
            box-shadow: 0 0 35px rgba(168,85,247,0.75) !important;
            transform: scale(1.02) !important;
        }

        /* 🔵 FORGOT PASSWORD — secondary form submit, Cyan glass */
        .stFormSubmitButton > button[kind="secondaryFormSubmit"] {
            background: rgba(34,211,238,0.18) !important;
            color: #22d3ee !important;
            border: 1.5px solid rgba(34,211,238,0.55) !important;
            height: 42px !important;
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            box-shadow: 0 0 14px rgba(34,211,238,0.3) !important;
        }
        .stFormSubmitButton > button[kind="secondaryFormSubmit"]:hover {
            background: rgba(34,211,238,0.32) !important;
            color: #ffffff !important;
        }

        /* ✨ ALL OUTER BUTTONS (New User, Back, Cancel) — Purple-Pink gradient glass */
        .stButton > button {
            background: linear-gradient(135deg, rgba(99,102,241,0.32), rgba(236,72,153,0.25)) !important;
            color: #ffffff !important;
            border: 1.5px solid #818cf8 !important;
            height: 50px !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            border-radius: 12px !important;
            box-shadow: 0 0 18px rgba(99,102,241,0.42) !important;
            backdrop-filter: blur(10px) !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, rgba(99,102,241,0.50), rgba(236,72,153,0.42)) !important;
            box-shadow: 0 0 30px rgba(99,102,241,0.65) !important;
            transform: translateY(-2px) !important;
        }
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
        with st.container():
            if st.session_state.auth_mode == "login":
                with st.form("login_form"):
                    st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'><span style='-webkit-text-fill-color: initial;'>🌟</span> Welcome Back</h3>", unsafe_allow_html=True)
                    email = st.text_input("Email", placeholder="yourname@gmail.com")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    
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
                            storage.save_pending_user(new_email, new_pass, otp)
                            if email_helper.send_otp_email(new_email, otp):
                                st.session_state.verifying_email = new_email
                                st.session_state.pending_pass = new_pass
                                st.rerun()

                col_btn_1, col_btn_2, col_btn_3 = st.columns([1, 4, 1])
                with col_btn_2:
                    if st.button("⬅ Back to Login", use_container_width=True):
                        st.session_state.auth_mode = "login"
                        st.rerun()

def show_verification_screen():
    st.markdown("""
<div style="text-align: center; margin-top: 10px; margin-bottom: 30px;">
<h1 class="auth-title-large">VERIFY</h1>
</div>
""", unsafe_allow_html=True)

    col_empty1, col_form, col_empty2 = st.columns([1, 2, 1])
    with col_form:
        with st.form("verify_form"):
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 25px;">
                <div style="background: rgba(16, 185, 129, 0.15); width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px; border: 1px solid rgba(16, 185, 129, 0.4);">
                    <span style="font-size: 2rem;">🛡️</span>
                </div>
                <h3 style="margin: 0; color: white;">Verify Email</h3>
                <p style="opacity: 0.7; font-size: 0.9rem; margin-top: 8px;">We sent a code to:<br><b>{st.session_state.verifying_email}</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            code = st.text_input("6-digit Code", placeholder="XXXXXX", label_visibility="collapsed")
            st.write("")
            submit = st.form_submit_button("VALIDATE & JOIN", use_container_width=True)
            
            if submit:
                user_id = storage.verify_otp(st.session_state.verifying_email, code)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.authenticated = True
                    st.session_state.verifying_email = None
                    st.rerun()
                else:
                    st.error("Invalid code.")
        
        st.write("")
        if st.button("⬅ Cancel & Back to Login", use_container_width=True):
            st.session_state.verifying_email = None
            st.rerun()

def show_reset_password_screen():
    st.markdown("""
<div style="text-align: center; margin-top: 10px; margin-bottom: 30px;">
<h1 class="auth-title-large">RECOVER</h1>
</div>
""", unsafe_allow_html=True)

    if not st.session_state.get("reset_step"):
        st.session_state.reset_step = 1

    col_empty1, col_form, col_empty2 = st.columns([1, 2, 1])
    with col_form:
        if st.session_state.reset_step == 1:
            with st.form("forgot_form"):
                st.markdown("""
                <div style="text-align: center; margin-bottom: 25px;">
                    <div style="background: rgba(244, 63, 94, 0.15); width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px; border: 1px solid rgba(244, 63, 94, 0.4);">
                        <span style="font-size: 2rem;">🔑</span>
                    </div>
                    <h3 style="margin: 0; color: white;">Reset Password</h3>
                    <p style="opacity: 0.7; font-size: 0.9rem; margin-top: 8px;">Enter your email to receive a recovery code.</p>
                </div>
                """, unsafe_allow_html=True)
                email = st.text_input("Registered Email", placeholder="yourname@gmail.com")
                st.write("")
                submit = st.form_submit_button("SEND RESET CODE", use_container_width=True)
                if submit:
                    if storage.email_exists(email):
                        otp = email_helper.generate_otp()
                        st.session_state.reset_email = email
                        st.session_state.reset_otp = otp
                        if email_helper.send_otp_email(email, otp):
                            st.session_state.reset_step = 2
                            st.rerun()
                    else:
                        st.error("Email not found.")
        
        elif st.session_state.reset_step == 2:
            with st.form("reset_verify"):
                st.markdown(f"""
                <div style="text-align: center; margin-bottom: 25px;">
                    <div style="background: rgba(99, 102, 241, 0.15); width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px; border: 1px solid rgba(99, 102, 241, 0.4);">
                        <span style="font-size: 2rem;">🛡️</span>
                    </div>
                    <h3 style="margin: 0; color: white;">Final Step</h3>
                    <p style="opacity: 0.7; font-size: 0.9rem; margin-top: 8px;">Check <b>{st.session_state.reset_email}</b> for the code.</p>
                </div>
                """, unsafe_allow_html=True)
                code = st.text_input("Recovery Code", placeholder="XXXXXX")
                new_pass = st.text_input("New Password", type="password", placeholder="••••••••")
                st.write("")
                submit = st.form_submit_button("UPDATE PASSWORD", use_container_width=True)
                if submit:
                    if code == st.session_state.reset_otp:
                        storage.reset_password(st.session_state.reset_email, new_pass)
                        st.success("Password Updated!")
                        st.session_state.auth_mode = "login"
                        st.session_state.reset_step = 1
                        st.rerun()
                    else:
                        st.error("Invalid Code.")

        st.write("")
        if st.button("⬅ Back to Login", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.session_state.reset_step = 1
            st.rerun()

if __name__ == "__main__":
    main()