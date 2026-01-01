# 🤖 DataOracle AI v1.0
> **Autonomous Healthcare Data Intelligence & Local Audit System.**

DataOracle AI is a local multi-agent system designed to transform raw clinical CSV data into executive-level intelligence. It audits data integrity, performs autonomous cleaning, and generates high-fidelity visualizations—all within your local environment.

---

## 🚀 Key Features

* **🕵️ Autonomous Data Auditor:** Scans local datasets for health scores, missing values, and statistical anomalies.
* **📊 Dynamic Visualization Engine:** Generates trend-focused plots based on real-world 2024-2025 healthcare shifts.
* **🧠 Multi-Agent Orchestration:** Powered by **LangGraph**, coordinating an Auditor, Coder, and Reporter node.
* **💬 AI Consultant:** A chat interface that allows you to ask deep-dive questions about your dataset.
* **📄 Executive PDF Export:** Automatically generates a structured PDF report of the findings.

---

## 🏗️ System Architecture

The application operates on a classic Client-Server model optimized for local data processing and speed.



1.  **Frontend:** A React (Vite) dashboard using Tailwind CSS for a modern, high-contrast UI.
2.  **Backend:** FastAPI handles the file processing and triggers the LangGraph AI state machine.
3.  **State Management:** Uses `MemorySaver` to track chat history within the current session.
4.  **Local Storage:** All plots and PDF reports are saved directly to the `static/` directory for immediate viewing.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React, Lucide Icons, Axios, Tailwind CSS |
| **Backend** | FastAPI, Uvicorn, LangGraph, LangChain |
| **AI Models** | Groq (Llama 3.3 70B) |
| **Data Engine** | Pandas, Matplotlib, Seaborn |
| **Reporting** | FPDF (Structured PDF Generation) |

---

## 📦 Installation & Setup

Follow these steps to get DataOracle AI running on your local machine.

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/dataoracle-ai.git](https://github.com/yourusername/dataoracle-ai.git)
cd dataoracle-ai


2. Backend Setup
Navigate to the backend folder, create a virtual environment, and install dependencies:

Bash

cd backend
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt

GROQ_API_KEY=your_groq_api_key_here

3. Frontend Setup
Open a new terminal, navigate to the frontend folder, and install dependencies:

Bash

cd frontend
npm install
npm run dev

├── backend/
│   ├── main.py              # FastAPI routes (Analyze & Chat)
│   ├── master_agent.py      # LangGraph AI nodes & workflow
│   ├── report_gen.py        # PDF report construction logic
│   ├── static/              # Local storage for plots and PDFs
│   └── requirements.txt     # Python libraries
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React Dashboard
│   │   └── index.css        # Tailwind styles
│   └── package.json         # Node dependencies
└── README.md
