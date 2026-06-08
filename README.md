# 🚀 AGENT FORGE OS
### Dynamic Multi-Tool AI Agent Orchestrator

> An AI-powered agent creation and deployment platform that transforms unstructured documents into actionable workflows across Google Workspace and SMTP ecosystems.

---

## 📌 Overview

Agent Forge OS is an automated AI agent creation and deployment platform that processes unstructured logs, invoices, and logistical narratives, then intelligently routes data payloads across live Google Workspace instances and secure SMTP networks.

The platform utilizes a customized **Traffic Cop Execution Framework** to:

- Parse incoming data streams
- Map authorized endpoints via persistent blueprint storage
- Enforce tool-level security boundaries
- Execute concurrent operations across:
  - Google Sheets
  - Google Docs
  - Google Slides
  - SMTP Email Systems

Agent Forge OS bridges the gap between conversational AI and real-world operational tooling where traditional automation pipelines struggle with variable document formats.

---

## 🏆 Hackathon Context

Built during the **InFynd Agent OS Hackathon**.

The project demonstrates autonomous workflow compilation, dynamic tool authorization, and secure execution using configurable AI agents.

---

# ✨ Core Features

## Dynamic Tool Blueprinting

Users create specialized agents through Agent Studio by defining:

- Agent identity
- Operational purpose
- Behavioral constraints
- Authorized tool permissions

---

## Traffic Cop Router

A secure orchestration layer that:

- Validates incoming payloads
- Checks agent permissions
- Restricts tool access
- Routes execution requests safely

---

## Context-Aware UI Rendering

The interface dynamically adapts based on the selected agent blueprint.

Examples:

- Google Sheets agent → Show spreadsheet fields
- Email agent → Show SMTP configuration
- Docs agent → Show document configuration

---

## Automated Tabular Extraction

Extracts structured financial data from unstructured text and updates:

- Google Sheets
- Pandas DataFrames
- Financial summaries

---

## Automated Document Stitching

Generates formatted narrative reports and operational summaries directly into:

- Google Docs

---

## Presentation Generation

Automatically creates structured presentation slides using:

- Google Slides API

---

## Automated SMTP Dispatch

Extracts contacts, builds tailored email content, and sends messages through secure SMTP channels.

---

# 🔄 Workflow Pipeline

## Step 1 — Agent Creation

Developers configure:

- Agent identity
- Purpose
- Behavioral rules
- Tool permissions

---

## Step 2 — Dynamic UI Adaptation

The interface reads the blueprint and displays only the fields required for that workflow.

---

## Step 3 — File Ingestion

Supported inputs:

- Invoices
- Reports
- Event Documents
- Operational Logs

---

## Step 4 — Autonomous Execution

```bash
User Upload
   │
   ▼
Flask Engine
   │
   ▼
Gemini 2.5 Flash
   │
   ▼
Payload Segmentation
   │
   ▼
Traffic Cop Validation
   │
   ▼
Tool Authorization
   │
   ▼
Google Workspace + SMTP
   │
   ▼
Live Dashboard Updates
```

## Step 5 — Execution Resolution

Simultaneously updates:

Dashboard logs
Google Sheets
Google Docs
Google Slides
SMTP notifications

## 🏗️ System Architecture
```bash
agent-forge-os/
│
├── static/
├── templates/
├── uploads/
│
├── app.py
├── database.py
├── executor.py
│
├── .env
├── credentials.json
└── requirements.txt
```

## 🛠️ Technology Stack
Technology	Purpose
Flask	Backend API & Application Engine
MongoDB	Blueprint Storage
Gemini 2.5 Flash	Structured Extraction & Intelligence
Pandas	Data Validation & Processing
GSpread	Google Sheets Integration
Google Docs API	Document Generation
Google Slides API	Presentation Generation
SMTP	Email Automation

## 🔐 Integration Mechanics
```json
Payload Segmentation Schema
{
  "analysis_report": "System display overview text",
  "csv_data": "Model,Qty,Price\nItemA,1,100.00",
  "doc_data": "Detailed analytical breakdown",
  "slide_data": [
    "Milestone 1",
    "Milestone 2"
  ]
}
```

### Security Enforcement

Unauthorized tool execution attempts are automatically blocked.

### 🚫 [WARN] Email Tool not equipped.
Bypassing SMTP execution.

## 🚀 Local Installation
Clone Repository
git clone https://github.com/YOUR-USERNAME/Agent-Forge.git
cd Agent-Forge
Create Virtual Environment
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
Configure Environment Variables

Create a .env file:

SECRET_KEY=your_secure_flask_token

MONGO_URI=your_mongodb_cluster_string

GEMINI_API_KEY=your_google_gemini_api_key

### Google Credentials
from API & SERVICES -> Service Accounts

Place:
credentials.json
in the project root directory.

Run Application
python app.py

## 🎯 Use Cases
Corporate Procurement Automation
Event & Hackathon Operations
QA Failure Monitoring
Automated Reporting Pipelines
Multi-Channel Communication Workflows

## 🔮 Future Enhancements
Multi-Agent Collaboration Chains
Vector Memory Integration
Slack Integration
Discord Integration
Jira Integration
GitHub Issues Integration
Ollama-Based Local LLM Support

# 👨‍💻 Authors

- **[Pranav S](https://github.com/your-pranav-github-username)**
- **[Sri Ram M](https://github.com/your-github-username)**

Computer Science Engineering Students  
Full Stack Developers 

Built with a focus on speed, scalability, automation, and real-world business usability.

## 📜 Disclaimer
This project is built strictly for educational, research, and hackathon evaluation purposes.
