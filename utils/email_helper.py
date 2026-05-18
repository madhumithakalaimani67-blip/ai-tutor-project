import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

def generate_otp():
    return f"{random.randint(100000, 999999)}"

def _send_email(to_email, subject, html_body):
    smtp_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_PORT", 465))
    smtp_user = os.getenv("EMAIL_USER", "")
    smtp_pass = os.getenv("EMAIL_PASS", "")

    if not smtp_user or not smtp_pass:
        return False, "Email credentials not set in .env"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"EDUAI <{smtp_user}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, to_email, msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, to_email, msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)


def send_otp_email(to_email, otp_code):
    load_dotenv()

    # Dev mode: show code on screen instead of sending
    dev_mode = os.getenv("DEV_MODE", "False").lower() == "true"
    if dev_mode:
        st.success("🛠️ Dev Mode enabled")
        st.info(f"💡 Verification Code: **{otp_code}**")
        return True

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;
                background:#0d1117;color:#e2e8f0;border-radius:16px;
                padding:32px;border:1px solid rgba(99,102,241,0.3);">
        <h2 style="background:linear-gradient(135deg,#6366f1,#a855f7);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   margin:0 0 8px 0;">EDUAI 🧠</h2>
        <p style="opacity:0.7;margin:0 0 24px 0;">Your AI Study Companion</p>
        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:0 0 24px 0;">
        <p>Your verification code is:</p>
        <div style="font-size:2.5rem;font-weight:900;letter-spacing:8px;
                    color:#6366f1;text-align:center;margin:16px 0;">{otp_code}</div>
        <p style="opacity:0.6;font-size:0.85rem;">Expires in 10 minutes. Do not share it.</p>
    </div>
    """

    ok, err = _send_email(to_email, "EDUAI Verification Code", html_body)
    if ok:
        st.success(f"✅ Code sent to {to_email}!")
    else:
        st.error(f"Email failed: {err}")
        # Fallback: show code on screen so user is never stuck
        st.info(f"🔍 Your code: **{otp_code}**")
    return True  # Always allow login flow to continue


def send_reminder_email(to_email, name, streak):
    load_dotenv()

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;
                background:#0d1117;color:#e2e8f0;border-radius:16px;
                padding:32px;border:1px solid rgba(99,102,241,0.3);">
        <h2 style="background:linear-gradient(135deg,#6366f1,#a855f7);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   margin:0 0 8px 0;">EDUAI 🧠</h2>
        <p style="opacity:0.7;margin:0 0 24px 0;">Don't break your streak!</p>
        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:0 0 24px 0;">
        <p>Hey <strong>{name}</strong> 👋</p>
        <p>Your streak is <strong style="color:#f59e0b;">🔥 {streak} days</strong>!
           Head back to EDUAI and lock in today's mission.</p>
        <p style="opacity:0.6;font-size:0.85rem;margin-top:24px;">— The EDUAI Team</p>
    </div>
    """

    ok, err = _send_email(to_email, "⏰ Don't Break Your Streak — EDUAI", html_body)
    if not ok:
        print(f"[EDUAI] Reminder email failed for {to_email}: {err}")
    return ok