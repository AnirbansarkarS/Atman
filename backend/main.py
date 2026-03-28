from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

# Import your other modules
# import brain_loader
# import brain_graphs
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
    # Load brain data on startup
    # brain_loader.load_data()
    print("FastAPI server started.")

@app.get("/api/brain-graph")
async def get_brain_graph():
    # Generate and return the brain graph
    # image_path = brain_graphs.generate_graph()
    # return FileResponse(image_path)
    # Placeholder response
    return {"message": "Brain graph endpoint"}


@app.post("/api/chat")
async def chat(message: dict):
    # Get response from AI persona
    # response = brain_persona.get_response(message.get("text"))
    # return {"response": response}
    # Placeholder response
    return {"response": "This is a response from the AI."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
