import os
import sys
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure repository root is on path so Test_AI can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.append(ROOT)

try:
    from Test_AI import setup_rag_pipeline
    from langchain_core.messages import HumanMessage, AIMessage
except Exception as e:
    setup_rag_pipeline = None
    HumanMessage = None
    AIMessage = None

app = FastAPI(title="InsightQ Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

DATA_DIR = os.environ.get("DOCUMENTS_DIR", os.path.join(ROOT, "documents"))
os.makedirs(DATA_DIR, exist_ok=True)

pipeline = None
chat_histories: Dict[str, List[Dict[str, str]]] = {}


@app.get("/")
def root():
    return {"status": "ok", "info": "InsightQ backend running"}


@app.get("/health")
def health():
    """Health endpoint for container orchestration. Returns basic service state.

    - pipeline_ready: whether the RAG pipeline has been built in memory
    - setup_available: whether the pipeline factory (setup_rag_pipeline) was importable
    """
    return {
        "status": "ok",
        "pipeline_ready": pipeline is not None,
        "setup_available": setup_rag_pipeline is not None,
    }


@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    saved = []
    try:
        for f in files:
            dest = os.path.join(DATA_DIR, f.filename)
            with open(dest, "wb") as out:
                content = await f.read()
                out.write(content)
            saved.append(f.filename)
        return {"saved": saved, "path": os.path.abspath(DATA_DIR)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/build")
def build():
    global pipeline, chat_histories
    if setup_rag_pipeline is None:
        return JSONResponse(status_code=500, content={"error": "setup_rag_pipeline not available. Check Test_AI.py import and dependencies."})
    try:
        pipeline = setup_rag_pipeline(DATA_DIR)
        chat_histories = {}
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/chat")
def chat(input: Dict[str, Any]):
    """Expected JSON: {"input": "question text", "chat_history": [{"role":"human|ai","content":"..."}], "session_id": "optional"} """
    global pipeline, chat_histories
    if pipeline is None:
        return JSONResponse(status_code=400, content={"error": "pipeline not built. POST /build first."})

    message = input.get("input") or input.get("message")
    session_id = input.get("session_id") or "default"
    incoming = input.get("chat_history", []) or []

    # Convert incoming history to LangChain message objects if available
    converted = []
    if HumanMessage is not None and AIMessage is not None:
        for turn in incoming:
            role = turn.get("role")
            content = turn.get("content")
            if role == "human":
                converted.append(HumanMessage(content=content))
            else:
                converted.append(AIMessage(content=content))
    else:
        # If message classes unavailable, pass empty history — pipeline may accept plain lists
        converted = incoming

    try:
        result = pipeline.invoke({"input": message, "chat_history": converted})
        # Build new history (server-side) by appending the latest turn
        new_history_msgs = []
        # We preserve the incoming turns as simple dicts
        for turn in incoming:
            new_history_msgs.append({"role": turn.get("role"), "content": turn.get("content")})
        new_history_msgs.append({"role": "human", "content": message})
        new_history_msgs.append({"role": "ai", "content": result})

        chat_histories[session_id] = new_history_msgs
        return {"response": result, "chat_history": new_history_msgs}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/history")
def history(session_id: Optional[str] = None):
    sid = session_id or "default"
    return {"session_id": sid, "history": chat_histories.get(sid, [])}
