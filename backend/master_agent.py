import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import operator
from datetime import datetime
from typing_extensions import TypedDict, List, Annotated, Dict, Any, Union
from scipy import stats
from fpdf import FPDF
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

load_dotenv()

# --- UTILITY: PDF SAFE TEXT ---
def clean_text(text):
    """Replaces Unicode characters that FPDF (latin-1) cannot handle."""
    if not text:
        return ""
    replacements = {
        '\u2011': '-', '\u2013': '-', '\u2014': '-',
        '\u2018': "'", '\u2019': "'", 
        '\u201c': '"', '\u201d': '"',
        '\u2022': '*', # Bullet points
    }
    text = str(text)
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text.encode('latin-1', 'ignore').decode('latin-1')

class AgentState(TypedDict):
    csv_path: str
    user_query: str                  
    data_profile: Dict[str, Any]     
    key_findings: List[str]          
    viz_results: List[Dict[str, Any]] 
    chat_history: Annotated[List[BaseMessage], operator.add]
    data_summary: str
    analysis_plan: List[Dict[str, str]]
    viz_code: str
    kpis: Dict[str, Any]
    external_context: str
    final_report: str
    error_log: str
    retry_count: int

# --- NODES ---

def profiler_node(state: AgentState):
    target_path = os.path.abspath(state['csv_path'])
    if not os.path.exists(target_path):
        return {"error_log": f"File not found at {target_path}", "retry_count": 5}

    df = pd.read_csv(target_path)
    profile = {
        "columns": {
            "numerical": list(df.select_dtypes(include=[np.number]).columns),
            "categorical": list(df.select_dtypes(include=['object']).columns),
        },
        "null_counts": df.isnull().sum().to_dict(),
        "uniques": {col: int(df[col].nunique()) for col in df.columns},
        "shape": df.shape,
        "sample": df.head(10).to_dict(orient='records')
    }
    summary = f"Dataset: {df.shape[0]} rows. Cols: {list(df.columns)}"
    return {
        "data_profile": profile, 
        "data_summary": summary, 
        "chat_history": [],
        "viz_results": [],
        "key_findings": [],
        "retry_count": 0
    }

def auditor_node(state: AgentState):
    df = pd.read_csv(state['csv_path'])
    health_score = int((1 - (df.isnull().sum().sum() / df.size)) * 100)
    grade = "A" if health_score > 90 else "B" if health_score > 75 else "C"
    profile = state['data_profile']
    profile['health_grade'] = grade
    profile['health_score'] = health_score
    return {"data_profile": profile}

def sanitizer_node(state: AgentState):
    df = pd.read_csv(state['csv_path'])
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            df[col] = df[col].fillna(df[col].median())
        else:
            if not df[col].mode().empty:
                df[col] = df[col].fillna(df[col].mode()[0])
    
    cleaned_path = "static/cleaned_data.csv"
    os.makedirs("static", exist_ok=True)
    df.to_csv(cleaned_path, index=False)
    return {"csv_path": cleaned_path, "error_log": "Data Sanitized."}

def kpi_node(state: AgentState):
    df = pd.read_csv(state['csv_path'])
    numeric = df.select_dtypes(include=[np.number])
    kpis = {
        "Total Records": len(df),
        "Key Metrics": numeric.mean().sort_values(ascending=False).head(3).to_dict()
    }
    return {"kpis": kpis}

def context_weaver_node(state: AgentState):
    llm = ChatGroq(model="openai/gpt-oss-120b")
    prompt = f"Given these data columns: {state['data_summary']}, suggest 2 real-world trends from 2024-2025 affecting these."
    response = llm.invoke(prompt)
    return {"external_context": response.content}

def strategist_node(state: AgentState):
    llm = ChatGroq(model="openai/gpt-oss-120b")
    system_msg = "You are a Lead Analyst. Plan 6 distinct plots. Output ONLY JSON list: [{'title': '...', 'goal': '...'}]"
    response = llm.invoke([SystemMessage(content=system_msg), HumanMessage(content=state['data_summary'])])
    
    try:
        clean_json = response.content.replace("```json", "").replace("```", "").strip()
        return {"analysis_plan": json.loads(clean_json)}
    except:
        return {"error_log": "Strategist JSON parsing failure"}

def coder_node(state: AgentState):
    llm = ChatGroq(model="openai/gpt-oss-120b")
    tasks = json.dumps(state['analysis_plan'])
    error_ctx = f"\nFIX THIS ERROR: {state['error_log']}" if state['error_log'] else ""
    
    system_msg = f"""Write Python code using Seaborn. 
    - Use 'df' (already loaded).
    - Save plots sequentially starting from 'static/plot_0.png'.
    - Use sns.set_theme(style='darkgrid').
    - Tasks: {tasks} {error_ctx}. 
    - Output RAW CODE ONLY (No Markdown)."""
    
    response = llm.invoke(system_msg)
    return {"viz_code": response.content.replace("```python", "").replace("```", "").strip()}

def executor_node(state: AgentState):
    df = pd.read_csv(state['csv_path'])
    os.makedirs("static", exist_ok=True)
    local_vars = {"df": df, "plt": plt, "sns": sns, "pd": pd, "np": np}
    
    try:
        plt.close('all')
        exec(state['viz_code'], {}, local_vars)
        results = [{"title": t['title'], "path": f"static/plot_{i}.png"} for i, t in enumerate(state['analysis_plan'])]
        return {"viz_results": results, "error_log": "", "retry_count": state['retry_count']+1}
    except Exception as e:
        return {"error_log": str(e), "retry_count": state['retry_count']+1}

def analyst_node(state: AgentState):
    llm = ChatGroq(model="openai/gpt-oss-120b")
    context = f"KPIs: {state['kpis']}\nResearch: {state['external_context']}\nPlots: {json.dumps(state['viz_results'])}"
    
    system_msg = """Output a JSON object: 
    {
      "findings": ["Finding 1", "Finding 2"], 
      "descriptions": {"static/plot_0.png": "Insight..."}
    }"""
    
    response = llm.invoke([SystemMessage(content=system_msg), HumanMessage(content=context)])
    try:
        data = json.loads(response.content.replace("```json", "").replace("```", "").strip())
    except:
        data = {"findings": ["Unable to parse findings"], "descriptions": {}}

    enriched = []
    for viz in state['viz_results']:
        viz['description'] = data['descriptions'].get(viz['path'], "Significant trend detected.")
        enriched.append(viz)
        
    return {"key_findings": data['findings'], "viz_results": enriched, "final_report": response.content}

def pdf_generator_node(state: AgentState):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, clean_text("Executive Intelligence Report"), ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, clean_text("Market & External Context:"), ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, clean_text(state.get('external_context', '')))
    
    for viz in state['viz_results'][:4]: 
        if os.path.exists(viz['path']):
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, clean_text(viz['title']), ln=True)
            pdf.image(viz['path'], x=10, y=30, w=180)
            pdf.ln(120)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 7, clean_text(viz['description']))
            
    report_path = "static/Executive_Report.pdf"
    pdf.output(report_path)
    return {"final_report": f"Report Generated: {report_path}"}

def follow_up_node(state: AgentState):
    llm = ChatGroq(model="openai/gpt-oss-120b")
    system_prompt = f"You are a Data Expert. Context: {state['data_profile']}. Previous findings: {state['key_findings']}. Answer the user question based on the provided data context."
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        *state.get('chat_history', []),
        HumanMessage(content=state['user_query'])
    ])
    return {"chat_history": [response]}

# --- ROUTING LOGIC ---

def route_start(state: AgentState):
    """Router to skip heavy analysis during follow-up chat."""
    # If user_query is present but csv_path is None, it's a follow-up
    if state.get("user_query") and not state.get("csv_path"):
        return "chat"
    return "profiler"

def router(state: AgentState):
    if state['error_log'] and state['retry_count'] < 3:
        return "retry"
    return "finalize"

# --- WORKFLOW ---
workflow = StateGraph(AgentState)

workflow.add_node("profiler", profiler_node)
workflow.add_node("auditor", auditor_node)
workflow.add_node("sanitizer", sanitizer_node)
workflow.add_node("kpi", kpi_node)
workflow.add_node("context", context_weaver_node)
workflow.add_node("strategist", strategist_node)
workflow.add_node("coder", coder_node)
workflow.add_node("executor", executor_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("pdf", pdf_generator_node)
workflow.add_node("chat", follow_up_node)

# --- Updated Entry Logic ---
workflow.set_conditional_entry_point(
    route_start,
    {
        "chat": "chat",
        "profiler": "profiler"
    }
)

# Standard Analysis Path
workflow.add_edge("profiler", "auditor")
workflow.add_edge("auditor", "sanitizer")
workflow.add_edge("sanitizer", "kpi")
workflow.add_edge("kpi", "context")
workflow.add_edge("context", "strategist")
workflow.add_edge("strategist", "coder")
workflow.add_edge("coder", "executor")
workflow.add_conditional_edges("executor", router, {"retry": "coder", "finalize": "analyst"})
workflow.add_edge("analyst", "pdf")
workflow.add_edge("pdf", END)

# Chat Path
workflow.add_edge("chat", END)

memory = InMemorySaver()
app = workflow.compile(checkpointer=memory)

print("Master Data Agent successfully compiled with original model names.")