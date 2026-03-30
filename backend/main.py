"""FastAPI application — main entry point for the Atman Uploaded Brain backend."""
import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

import brain_graphs
import brain_loader
import brain_persona

app = FastAPI(title="Atman — Uploaded Brain API")

# --------------------------------------------------------------------------- #
# CORS                                                                        #
# --------------------------------------------------------------------------- #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# Startup                                                                     #
# --------------------------------------------------------------------------- #
@app.on_event("startup")
async def startup_event():
    print("🧠 Atman backend running on :8000")


# --------------------------------------------------------------------------- #
# Status endpoint — returns real EEG metadata once data is loaded             #
# --------------------------------------------------------------------------- #
@app.get("/api/status")
async def get_status():
    return brain_loader.get_stats()


# --------------------------------------------------------------------------- #
# Load endpoint — SSE progress stream while loading EEG from disk             #
# --------------------------------------------------------------------------- #
@app.get("/api/load")
async def load_brain(subject: str = "01"):
    """
    Server-Sent Events stream that loads EEG data and reports progress.
    Frontend subscribes with EventSource('/api/load').
    """
    async def event_generator():
        def send(data: dict) -> str:
            return f"data: {json.dumps(data)}\n\n"

        yield send({"status": "init", "progress": 5, "message": "Locating neural substrate…"})
        await asyncio.sleep(0.3)

        # Run blocking I/O in thread pool so we don't block the event loop
        loop = asyncio.get_event_loop()
        yield send({"status": "loading", "progress": 20, "message": "Reading BDF file…"})
        await asyncio.sleep(0.1)

        try:
            info = await loop.run_in_executor(
                None,
                lambda: brain_loader.load_raw_data(subject=subject)
            )
            yield send({"status": "loading", "progress": 60, "message": "Preprocessing signals…"})
            await asyncio.sleep(0.3)

            stats = brain_loader.get_stats(subject=subject)
            yield send({"status": "loading", "progress": 85, "message": "Calibrating electrodes…"})
            await asyncio.sleep(0.3)

            yield send({
                "status": "ready",
                "progress": 100,
                "message": "Neural substrate loaded.",
                **stats,
            })
        except FileNotFoundError as exc:
            yield send({"status": "error", "progress": 0, "message": str(exc)})
        except Exception as exc:
            yield send({"status": "error", "progress": 0, "message": f"Load failed: {exc}"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# --------------------------------------------------------------------------- #
# Graph endpoint — returns PNG for one of the 4 graph types                  #
# --------------------------------------------------------------------------- #
@app.get("/api/graph")
async def get_brain_graph(type: str = "eeg", subject: str = "01"):
    loop = asyncio.get_event_loop()
    image_path: Path | None = await loop.run_in_executor(
        None,
        lambda: brain_graphs.generate_graph(type, subject=subject)
    )
    if image_path and image_path.exists():
        return FileResponse(path=str(image_path), media_type="image/png")
    raise HTTPException(status_code=500, detail=f"Failed to generate '{type}' graph")


# --------------------------------------------------------------------------- #
# Chat endpoint                                                               #
# --------------------------------------------------------------------------- #
@app.post("/api/chat")
def chat(payload: dict):
    user_message = payload.get("message", "")
    context = payload.get("context", {})

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    return StreamingResponse(
        brain_persona.get_response_stream(user_message, context),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


# --------------------------------------------------------------------------- #
# Inject endpoint                                                             #
# --------------------------------------------------------------------------- #
@app.post("/api/inject")
async def inject(payload: dict):
    word = payload.get("word", "").strip()
    context = payload.get("context", {})

    if not word:
        raise HTTPException(status_code=400, detail="No word provided")

    loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(
        None,
        lambda: brain_persona.get_inject_response(word, context)
    )
    return {"reply": reply}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
