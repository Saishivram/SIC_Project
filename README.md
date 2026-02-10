# Diabetes Risk & Guidance System (Hybrid AI Agent)

This project is an AI-powered clinical decision-support prototype that combines:

- Neural Networks (TensorFlow/Keras)
- Retrieval-Augmented Generation (FAISS)
- Azure OpenAI (LLM + Embeddings)
- Report Generation (ReportLab)
- Agent-based Email Delivery (Semantic Kernel concept)
- Flask Backend APIs

The system predicts diabetes risk from patient vitals, generates a structured medical report, allows chatting with the report, and sends the report via email.

---

## System Architecture

User Input → Neural Network → Risk Score  
Risk Score + Medical Guidelines → RAG → LLM Report  
Report → PDF Generator  
PDF → FAISS Index  
User Chat → Report QA  
Agent → Email Report  

---

## Features

- Diabetes risk prediction using PIMA dataset model
- Retrieval-Augmented medical guidance
- Automated clinical report generation (PDF)
- Chat with generated report
- Agent-based email delivery
- Flask API backend

---

## Project Structure

```

project/
│
├── app.py
├── report_chat.py
├── email_agent.py
├── agent_runner.py
│
├── diabetes_model.keras
├── scaler.save
├── diabetes_index.faiss
├── texts.pkl
│
├── requirements.txt
└── .env

````

---

## Installation

### 1. Clone repository
```bash
git clone <repo_url>
cd project
````

---

### 2. Create virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the root directory.

Example:

```
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/

EMAIL_USER=youremail@gmail.com
EMAIL_PASS=your_app_password
```

---

## Running the Server

```bash
python app.py
```

Server runs at:

```
http://127.0.0.1:5000
```

---

## API Usage

### Predict + Generate Report

POST `/predict`

```json
{
  "pregnancies":2,
  "glucose":150,
  "bp":70,
  "skin":20,
  "insulin":85,
  "bmi":30.5,
  "dpf":0.5,
  "age":45,
  "email":"user@example.com"
}
```

Returns:

* Email sent
* Report indexed for chat

---

### Download Report

GET `/download`

Returns:

* Genrated Report

---

### Chat with Report

POST `/chat`

```json
{
  "question": "Why am I at high risk?"
}
```

---

## Dependencies

* Flask
* TensorFlow
* FAISS
* ReportLab
* PyMuPDF
* python-dotenv
* Azure OpenAI SDK
* Semantic Kernel (agent logic)
* NumPy
* Joblib

---

## Notes

This project is for **educational and demonstration purposes only**.
It does not provide medical diagnosis.


