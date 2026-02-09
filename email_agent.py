import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

def send_report_email(to_email, pdf_path):
    msg = EmailMessage()
    msg["Subject"] = "Your Diabetes Risk Report"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = to_email

    msg.set_content(
        "Please find attached your diabetes risk assessment report."
    )

    with open(pdf_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename="report.pdf"
        )

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(
            os.getenv("EMAIL_USER"),
            os.getenv("EMAIL_PASS")
        )
        smtp.send_message(msg)
