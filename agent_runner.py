import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from email_agent import send_report_email
import os
from dotenv import load_dotenv

load_dotenv()

kernel = sk.Kernel()

kernel.add_service(
    AzureChatCompletion(
        service_id="chat",
        deployment_name="gpt-4o-mini",
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY")
    )
)

def run_email_agent(email, pdf_path):

    send_report_email(email, pdf_path)
