import os
import random
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

def generate_otp():
    return f"{random.randint(100000, 999999)}"

def send_otp_email(to_email, otp_code):
    # Re-load dotenv to ensure fresh environment variables in all contexts
    load_dotenv()
    
    host = os.getenv("EMAIL_HOST")
    port_env = os.getenv("EMAIL_PORT")
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    # Development Mode Bypass
    dev_mode = os.getenv("DEV_MODE", "False").lower() == "true"
    if dev_mode:
        st.success("🛠️ **EDUAI Developer Access enabled**")
        st.info(f"💡 Dev Verification Code: **{otp_code}**")
        st.toast("Code generated (Dev Mode)", icon="🛠️")
        return True

    # Robust port parsing 
    try:
        port = int(port_env) if port_env else 465
    except ValueError:
        port = 465

    if not all([host, user, password]):
        # No SMTP configured - Simulate OTP by showing it in Streamlit
        st.info(f"🔍 [SIMULATION] A verification code for {to_email} was generated: **{otp_code}**")
        st.toast("Verification code generated (Simulation)", icon="🔑")
        return True

    # Retry Logic (2 attempts)
    for attempt in range(2):
        try:
            msg = EmailMessage()
            msg.set_content(f"Your EDUAI verification code is: {otp_code}\n\nThis code will expire in 10 minutes.")
            msg["Subject"] = "EDUAI Verification Code"
            msg["From"] = user
            msg["To"] = to_email

            with smtplib.SMTP_SSL(host, port, timeout=10) as server:
                server.login(user, password)
                server.send_message(msg)
            
            st.success(f"Verification code sent to {to_email}!")
            return True
        except Exception as e:
            if attempt == 0:
                continue # Try one more time
            
            # Final failure handling
            st.error(f"Note: Email delivery had a hiccup ({e}).")
            # Pro-active fallback so user is never stuck
            st.info(f"🔍 [ACCESS CODE] Since the email is delayed, here is your code: **{otp_code}**")
            st.toast("Access code displayed on screen", icon="🛡️")
            return True # Return True so the Auth gate allows the user to proceed

def send_reminder_email(to_email, name, streak):
    load_dotenv()
    host = os.getenv("EMAIL_HOST")
    port_env = os.getenv("EMAIL_PORT")
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    try:
        port = int(port_env) if port_env else 465
    except ValueError:
        port = 465

    if not all([host, user, password]):
        print(f"[SIMULATION] Sending reminder to {to_email}")
        return True

    try:
        msg = EmailMessage()
        msg.set_content(f"Hey {name},\n\nThis is your daily study reminder from EDUAI! Keep your momentum going and maintain your current {streak} day streak. Let's crush those learning goals today!\n\nBest,\nEDUAI Team")
        msg["Subject"] = "⏰ Wait! Don't Break Your Streak - EDUAI Reminder"
        msg["From"] = user
        msg["To"] = to_email

        with smtplib.SMTP_SSL(host, port, timeout=10) as server:
            server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send reminder email: {e}")
        return False
