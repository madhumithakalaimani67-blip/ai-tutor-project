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
    host = os.getenv("EMAIL_HOST")
    port = os.getenv("EMAIL_PORT")
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    if not all([host, port, user, password]):
        # No SMTP configured - Simulate OTP by showing it in Streamlit
        st.info(f"🔍 [SIMULATION] A verification code for {to_email} was generated: **{otp_code}**")
        st.toast("Verification code generated (Simulation)", icon="🔑")
        return True

    try:
        msg = EmailMessage()
        msg.set_content(f"Your EDUAI verification code is: {otp_code}\n\nThis code will expire in 10 minutes.")
        msg["Subject"] = "EDUAI Verification Code"
        msg["From"] = user
        msg["To"] = to_email

        with smtplib.SMTP_SSL(host, int(port)) as server:
            server.login(user, password)
            server.send_message(msg)
        
        st.success(f"Verification code sent to {to_email}!")
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        # Fallback to simulation for the user
        st.info(f"🔍 [FALLBACK SIMULATION] Code: **{otp_code}**")
        return False
