import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "AI Interview Room")

def send_interview_email(to_email, candidate_name, interview_time, interview_link):
    if not SMTP_USER or not MAIL_PASSWORD:
        print("[WARNING] SMTP credentials not set. Email not sent.")
        print(f"Link: {interview_link}")
        return False

    msg = MIMEMultipart()
    msg['From'] = SMTP_FROM
    msg['To'] = to_email
    msg['Subject'] = f"AI Interview Invitation - {candidate_name}"

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 8px; max-width: 600px; margin: auto; }}
            .header {{ background-color: #4A90E2; color: white; padding: 10px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ padding: 20px; }}
            .button {{ display: inline-block; padding: 10px 20px; color: white; background-color: #4A90E2; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>Interview Invitation</h1></div>
            <div class="content">
                <p>Hello {candidate_name},</p>
                <p>You have been invited for an AI Interview.</p>
                <p><strong>Time:</strong> {interview_time}</p>
                <p>Please use the link below to join the interview at the scheduled time. 
                Note that you won't be able to join before or significantly after the slot.</p>
                <a href="{interview_link}" class="button">Join Interview</a>
                <p>Good luck!</p>
            </div>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, MAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False
