import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def test_email():
    host = os.getenv("EMAIL_HOST")
    port = os.getenv("EMAIL_PORT")
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    
    print(f"Connecting to {host}:{port} as {user}...")
    
    msg = EmailMessage()
    msg.set_content("Test email from EDUAI debug script.")
    msg["Subject"] = "EDUAI SMTP Test"
    msg["From"] = user
    msg["To"] = user # Send to self
    
    try:
        with smtplib.SMTP_SSL(host, int(port)) as server:
            server.login(user, password)
            server.send_message(msg)
        print("Success! Email sent.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_email()
