# app/main.py
from fastapi import FastAPI, Request, Header, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="RethinkAI Crime Rates API", version="1.0")

# -------------------------------
# MODELS
# -------------------------------

class ChatRequest(BaseModel):
    user_message: str
    client_query: Optional[str] = None
    prompt_preamble: Optional[str] = None
    data_attributes: Optional[Dict[str, Any]] = None

class ContextRequest(BaseModel):
    context_request: Optional[str] = None
    option: Optional[str] = None  # e.g., 'clear'

class SummaryRequest(BaseModel):
    messages: List[Dict[str, str]]

class IdentifyPlacesRequest(BaseModel):
    message: str

class LogEntry(BaseModel):
    data_selected: Optional[str] = None
    client_query: Optional[str] = None
    app_response: Optional[str] = None
    log_id: Optional[int] = None

# -------------------------------
# AUTH MIDDLEWARE
# -------------------------------

API_KEY_HEADER = "RethinkAI-API-Key"
VALID_KEYS = {"demo-key"}  # Replace with env variable or DB lookup

async def authenticate(api_key: Optional[str]):
    if api_key not in VALID_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized")

# -------------------------------
# ROUTES
# -------------------------------

@app.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    api_key: Optional[str] = Header(None),
    context_request: Optional[str] = Query(None),
    is_spatial: Optional[bool] = Query(False)
):
    await authenticate(api_key)
    # TODO: Integrate LLM + optional geospatial augmentation
    return {
        "response": f"Generated LLM response for: {request.user_message}",
        "context_used": context_request,
        "is_spatial": is_spatial
    }

@app.get("/chat/context")
@app.post("/chat/context")
async def context_endpoint(
    req: Optional[ContextRequest] = None,
    api_key: Optional[str] = Header(None),
    context_request: Optional[str] = Query(None)
):
    await authenticate(api_key)

    if req and req.option == "clear":
        # TODO: Clear cached contexts
        return {"message": "Caches cleared"}

    if context_request:
        # TODO: Token count or create new cache
        return {"context_request": context_request, "token_count": 1234}

    return {"available_caches": ["cache1", "cache2"]}

@app.post("/chat/summary")
async def summarize_chat(req: SummaryRequest, api_key: Optional[str] = Header(None)):
    await authenticate(api_key)
    # TODO: Summarize chat messages via LLM
    return {"summary": "This is a summary of your chat."}

@app.post("/chat/identify_places")
async def identify_places(req: IdentifyPlacesRequest, api_key: Optional[str] = Header(None)):
    await authenticate(api_key)
    # TODO: Run LLM prompt for place extraction
    return {"places": ["Boston", "Cambridge"]}

@app.get("/data/query")
@app.post("/data/query")
async def data_query(
    api_key: Optional[str] = Header(None),
    request: str = Query(...),
    category: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    zipcode: Optional[str] = Query(None),
    output_type: Optional[str] = Query("json"),
    is_spatial: Optional[bool] = Query(False)
):
    await authenticate(api_key)
    # TODO: Query MySQL and return data
    return {"query": request, "category": category, "data": [{"sample": "data"}]}

@app.post("/log")
@app.put("/log")
async def log_entry(req: LogEntry, api_key: Optional[str] = Header(None)):
    await authenticate(api_key)
    if req.log_id:
        # TODO: Update existing log
        return {"message": f"Updated log {req.log_id}"}
    # TODO: Insert new log
    return {"message": "New log created"}

@app.get("/llm_summaries")
async def get_llm_summary(
    month: str = Query(...),
    api_key: Optional[str] = Header(None)
):
    await authenticate(api_key)
    # TODO: Fetch precomputed summary from DB
    return {"month": month, "summary": "Summary text here"}

@app.get("/llm_summaries/all")
async def get_all_summaries(api_key: Optional[str] = Header(None)):
    await authenticate(api_key)
    # TODO: Return all summaries
    return {"summaries": [{"month": "2025-01", "summary": "example"}]}

# -------------------------------
# ROOT & HEALTH
# -------------------------------

@app.get("/")
def root():
    return {"message": "RethinkAI Crime Rates API running"}

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
