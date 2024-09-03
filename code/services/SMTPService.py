import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlencode
from services.hashService import generate_reset_token
import os

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_SUBJECT = 'Password Reset Request'

async def send_reset_email(email_to: str, reset_link: str, fullname: str):
    msg = MIMEMultipart()
    msg['Subject'] = EMAIL_SUBJECT
    msg['From'] = EMAIL_FROM
    msg['To'] = email_to

    template_dir = os.path.dirname(__file__)
    rel_path = "../Templates/reset.html"
    abs_file_path = os.path.join(template_dir, rel_path)
    
    with open(abs_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    html_content = html_content.replace("$(fullname)", fullname)
    html_content = html_content.replace("$(resetlink)", reset_link)
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM, email_to, msg.as_string())
        server.quit()

    except Exception as e:
        raise e

def generate_reset_link(user_email: str) -> str:
    base_url = os.getenv("RESET_BASE_URL")
    token = generate_reset_token(user_email)
    query_params = urlencode({"email": user_email, "token": token})
    return f"{base_url}?{query_params}"
