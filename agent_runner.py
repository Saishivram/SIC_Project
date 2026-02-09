import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from email_agent import send_report_email
import os

kernel = sk.Kernel()

kernel.add_service(
    AzureChatCompletion(
        service_id="chat",
        deployment_name="gpt-4o-mini",
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
    )
)

def run_email_agent(email, pdf_path, risk):

    # Agent reasoning prompt
    instruction = f"""
    A patient report has been generated.

    Risk score category: {risk}

    Decide whether to send the report via email.
    If risk is Moderate or High, send email.
    Otherwise do nothing.
    """

    # Simple agent reasoning
    if risk > 0.3:
        send_report_email(email, pdf_path)
