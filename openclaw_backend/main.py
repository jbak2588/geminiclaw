import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import our websocket router
from api.websockets import router as ws_router

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Agentic Team Orchestrator",
    description="Backend engine for the CTO-driven Gemini Agent platform.",
    version="1.0.0"
)

# Configure CORS for local development (allow Flutter or React app to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the WebSocket routing
app.include_router(ws_router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Agentic Team Engine is running."}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
