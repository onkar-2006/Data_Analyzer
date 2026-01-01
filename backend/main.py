import os
import uuid
import shutil
import traceback
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv()

# --- CONFIGURATION ---
API_BASE_URL = "http://localhost:8000"

try:
    from master_agent import app as agent_executor
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import 'agent_executor' from 'master_agent.py'.")
    print(f"Details: {e}")
    raise e

app = FastAPI(title="DataOracle AI: Autonomous API")

# --- 1. CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React Dev Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. STORAGE SETUP ---
os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Mount static folder so images/PDFs are accessible via URL
app.mount("/static", StaticFiles(directory="static"), name="static")

if not os.getenv("GROQ_API_KEY"):
    print("⚠️  WARNING: 'GROQ_API_KEY' environment variable is not set!")

# --- 3. DATA MODELS ---
class ChatRequest(BaseModel):
    thread_id: str
    user_query: str

# --- 4. ENDPOINTS ---

@app.post("/analyze")
async def start_analysis(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    thread_id = str(uuid.uuid4())
    # Save with unique ID to prevent filename collisions
    file_path = os.path.join("uploads", f"{thread_id}_{file.filename}")

    print(f"📂 Received file: {file.filename} (Session: {thread_id})")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        config = {"configurable": {"thread_id": thread_id}}
        # Initial input includes the CSV path to trigger the full pipeline
        initial_input = {"csv_path": file_path, "user_query": None}
        
        print(f"🧠 Agent is starting analysis for {file_path}...")
        
        # Invoke LangGraph Agent
        final_state = agent_executor.invoke(initial_input, config=config)

        # --- Convert relative paths to Absolute URLs for React ---
        viz_results = final_state.get("viz_results", [])
        for viz in viz_results:
            if viz.get('path'):
                # Handle Windows/Linux pathing and ensure absolute URL
                clean_path = viz['path'].replace("\\", "/").lstrip("/")
                viz['path'] = f"{API_BASE_URL}/{clean_path}"

        print(f"✅ Analysis Complete for {thread_id}")

        return {
            "thread_id": thread_id,
            "data_profile": final_state.get("data_profile", {}),
            "key_findings": final_state.get("key_findings", ["No findings generated."]),
            "viz_results": viz_results,
            "pdf_report_url": f"{API_BASE_URL}/static/Executive_Report.pdf", 
            "status": "Success"
        }

    except Exception as e:
        print("\n" + "="*50)
        print(" AGENT CRASHED DURING ANALYSIS")
        traceback.print_exc() 
        print("="*50 + "\n")
        raise HTTPException(status_code=500, detail=f"Internal Agent Error: {str(e)}")


@app.post("/chat")
async def follow_up_chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    try:
        print(f"💬 Chat Query: {request.user_query}")
        
        # ERROR FIX: Explicitly pass csv_path as None. 
        # This tells the router in master_agent.py to skip to the 'chat' node.
        result = agent_executor.invoke(
            {"user_query": request.user_query, "csv_path": None}, 
            config=config
        )

        messages = result.get("chat_history", [])
        if messages:
            # Result from follow_up_node is a list containing the new message
            last_message = messages[-1].content
        else:
            last_message = "Agent responded, but no message content was found."

        return {
            "answer": last_message,
            "thread_id": request.thread_id
        }

    except Exception as e:
        print("\n" + "="*50)
        print(" CHAT AGENT CRASHED")
        traceback.print_exc()
        print("="*50 + "\n")
        raise HTTPException(status_code=500, detail=f"Chat Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 DataOracle AI Backend is launching...")
    # Using 'main:app' allows reload to work correctly
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)