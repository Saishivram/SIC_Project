import numpy as np
import pickle
import faiss
import joblib
import tensorflow as tf
from flask import Flask, request, send_file
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import datetime
import json

# PDF
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

from report_chat import build_report_index, search_report

from agent_runner import run_email_agent

from flask import render_template

load_dotenv()

latest_report = None
#################################################
# LOAD ARTIFACTS
#################################################

DIM = 1536
TOP_K = 5

model = tf.keras.models.load_model("diabetes_model.keras")
scaler = joblib.load("scaler.save")

index = faiss.read_index("diabetes_index.faiss")
texts = pickle.load(open("texts.pkl", "rb"))

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-15-preview"
)

app = Flask(__name__, template_folder="templates", static_folder="static")

#################################################
# HELPER FUNCTIONS
#################################################

def embed(text):
    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(res.data[0].embedding).astype("float32")


def retrieve_context(query):
    q = embed(query).reshape(1, -1)
    _, I = index.search(q, TOP_K)
    return "\n".join([texts[i] for i in I[0]])


def predict_risk(features):
    arr = scaler.transform([features])
    return float(model.predict(arr)[0][0])

def generate_guidance(risk, context):

    tier = (
        "Low Risk" if risk < 0.3 else
        "Moderate Risk" if risk < 0.6 else
        "High Risk"
    )

    prompt = f"""
    You are generating a formal patient-facing clinical report.
    The goal is to EDUCATE and INFORM the patient clearly.

    Risk score: {risk*100:.1f}% ({tier})

    Guidelines:
    {context}

    Instructions:

    • Each section must be detailed (5–7 sentences minimum)
    • Explain WHY the patient is at risk
    • Explain WHAT the patient should do
    • Use professional but patient-friendly language
    • Avoid bullet points
    • Write full paragraphs
    • Provide educational explanation
    • Do NOT be brief

    Return ONLY JSON:

    {{
      "interpretation": "Explain what the risk score means clinically and why the patient is high risk.",
      "recommendations": "Provide evidence-based medical and guideline recommendations with reasoning.",
      "lifestyle": "Explain diet, exercise, weight control, and behavioral modifications in detail.",
      "preventive_actions": "Describe screenings, monitoring, prevention programs, and protective steps.",
      "follow_up": "Explain follow-up schedule, monitoring plan, and long-term care approach."
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content

    try:
        return json.loads(raw)
    except:
        # fallback → never crash
        return {
            "interpretation": raw,
            "recommendations": raw,
            "lifestyle": raw,
            "preventive_actions": raw,
            "follow_up": raw
        }


#################################################
# PDF GENERATION
#################################################


def create_pdf(filename, features, risk, advice, patient_name, patient_email):

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    #################################################
    # STYLES
    #################################################
    title_style = ParagraphStyle(
        "title",
        fontSize=22,
        textColor=colors.white,
        alignment=1
    )

    section_style = ParagraphStyle(
        "section",
        fontSize=15,
        textColor=colors.HexColor("#0b3c5d"),
        spaceBefore=20,
        spaceAfter=10
    )

    body_style = ParagraphStyle(
        "body",
        fontSize=11,
        leading=16,
        alignment=4
    )

    small_style = ParagraphStyle(
        "small",
        fontSize=9
    )

    #################################################
    # HEADER
    #################################################
    page_width = A4[0] - doc.leftMargin - doc.rightMargin
    title_style = ParagraphStyle(
        "title",
        fontSize=24,
        leading=30,
        textColor=colors.white,
        alignment=1
    )

    header_text=Paragraph("Review on the Data Shared", title_style)

    header = Table(
        [[header_text]],
        colWidths=[page_width],
        rowHeights=[50]
    )

    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0b3c5d")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1),0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0)
    ]))


    story.append(header)
    story.append(Spacer(1, 20))

    story.append(Paragraph(f"<b>Patient Name:</b> {patient_name}", body_style))
    story.append(Paragraph(f"<b>Email:</b> {patient_email}", body_style))
    story.append(Spacer(1, 10))


    story.append(Paragraph(
        f"<b>Generated On:</b> {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}",
        small_style
    ))

    #################################################
    # VITALS TABLE
    #################################################
    story.append(Paragraph("Clinical Measurements", section_style))

    labels = [
        "Pregnancies", "Glucose", "Blood Pressure", "Skin Thickness",
        "Insulin", "BMI", "Diabetes Pedigree Function", "Age"
    ]

    data = [["Parameter", "Value"]]
    for l, v in zip(labels, features):
        data.append([l, str(v)])

    table = Table(data, colWidths=[4 * inch, 3 * inch])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b3c5d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "CENTER")
    ]))

    story.append(table)

    #################################################
    # RISK BADGE
    #################################################
    story.append(Paragraph("Risk Assessment", section_style))

    if risk < 0.3:
        color = colors.green
        label = "LOW RISK"
    elif risk < 0.6:
        color = colors.orange
        label = "MODERATE RISK"
    else:
        color = colors.red
        label = "HIGH RISK"

    risk_box = Table(
        [[Paragraph(f"Predicted Probability: {risk*100:.2f}% ({label})", body_style)]],
        colWidths=[7 * inch]
    )

    risk_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("INNERPADDING", (0, 0), (-1, -1), 10)
    ]))

    story.append(risk_box)

    #################################################
    # GUIDANCE SECTIONS
    #################################################

    def add_section(title, content):

        elements = []

        elements.append(Spacer(1, 15))
        title_inner_style = ParagraphStyle(
            "title_inner",
            parent=section_style,
            fontSize=13,
            textColor=colors.HexColor("#0b3c5d"),
            leftIndent=5
        )

        data = [
            [Paragraph(f"<b>{title}</b>", title_inner_style)],
            [Paragraph(content, body_style)]
        ]

        section_table = Table(data, colWidths=[page_width])   
        section_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#e8f0f8")),
            ("TOPPADDING", (0, 0), (0, 0), 10),
            ("BOTTOMPADDING", (0, 0), (0, 0), 10),
            ("TOPPADDING", (0, 1), (0, 1), 15),
            ("BOTTOMPADDING", (0, 1), (0, 1), 15),
            ("LEFTPADDING", (0, 1), (0, 1), 15),
            ("RIGHTPADDING", (0, 1), (0, 1), 15),
            
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("LINEBELOW", (0, 0), (0, 0), 0.5, colors.grey), 
    ]))
        elements.append(section_table)
        story.append(KeepTogether(elements))


    add_section("Clinical Interpretation", advice.get("interpretation", ""))
    add_section("Guideline-Based Recommendations", advice.get("recommendations", ""))
    add_section("Lifestyle & Dietary Measures", advice.get("lifestyle", ""))
    add_section("Preventive Actions", advice.get("preventive_actions", ""))
    add_section("Follow-Up Advice", advice.get("follow_up", ""))

    #################################################
    # DISCLAIMER
    #################################################
    story.append(Spacer(1, 25))
    disclaimer_text = (
        "Medical Disclaimer: This report is AI-assisted and based on statistical analysis "
        "and publicly available medical guidelines. It is intended for educational and "
        "decision-support purposes only and must not be considered a definitive medical "
        "diagnosis. Consultation with a licensed healthcare professional is strongly recommended."
    )

    story.append(Paragraph(disclaimer_text, small_style))


    doc.build(story)

#################################################
# FLASK ROUTE
#################################################

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    global latest_report
    data = request.json

    patient_name = data["name"]
    patient_email = data["email"]


    features = [
        float(data["pregnancies"]),
        float(data["glucose"]),
        float(data["bp"]),
        float(data["skin"]),
        float(data["insulin"]),
        float(data["bmi"]),
        float(data["dpf"]),
        float(data["age"])
    ]

    # Neural network
    risk = predict_risk(features)

    # RAG
    context = retrieve_context("diabetes prevention guidelines")

    # LLM
    advice = generate_guidance(risk, context)

    # PDF
    filename = f"report_{datetime.datetime.now().timestamp()}.pdf"
    create_pdf(filename, features, risk, advice, patient_name, patient_email)
    build_report_index(filename, embed)
    run_email_agent(data["email"], filename,risk)
    latest_report = filename
    return {"message": "Report generated and emailed successfully",
            "risk": risk}

@app.route("/download", methods=["GET"])
def download():

    if not latest_report:
        return {"error": "No report generated yet"}, 400

    return send_file(latest_report, as_attachment=True)


@app.route("/chat", methods=["POST"])
def chat():

    question = request.json["question"]

    context = search_report(question, embed)

    prompt = f"""
    Answer the user's question using the report.
    Format the response as plain text paragraphs only.
    Do NOT use bullet points or numbered lists.
    Keep it concise and readable.

    Report context:
    {context}

    Question:
    {question}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return {"answer": response.choices[0].message.content}

#################################################
# RUN
#################################################

if __name__ == "__main__":
    app.run(debug=True)
