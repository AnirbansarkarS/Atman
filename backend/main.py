from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

import brain_graphs
# import brain_persona

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("FastAPI server started.")

@app.get("/api/status")
async def get_status():
    return {
        "trials": 320,
        "channels": 64,
        "hz": 1000
    }

@app.get("/api/graph")
async def get_brain_graph(type: str = "eeg"):
    # Depending on type, you'd generate the right graph. Here we'll fallback to a generic or eeg graph.
    image_path = brain_graphs.generate_graph()
    if image_path:
        return FileResponse(path=image_path, media_type="image/png")
    raise HTTPException(status_code=500, detail="Failed to generate brain graph")

@app.post("/api/inject")
async def inject(payload: dict):
    word = payload.get("word", "")
    return {"reply": f"You injected the concept '{word}'. It brings back strong associations."}

@app.post("/api/chat")
async def chat(payload: dict):
    user_message = payload.get("message", "")
    # Placeholder response
    return {"reply": f"I am simulating a response to: '{user_message}'."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
