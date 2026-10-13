from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import StreamingResponse
from pipeline import run_pipeline
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from services import start_speech
from pipeline import SESSION_HISTORY
from contextlib import asynccontextmanager
from db.models import Base
from db.session import engine
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
   await asyncio.to_thread(Base.metadata.create_all, bind=engine)
   yield
   await asyncio.to_thread(engine.dispose)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get_ui():
  return FileResponse("src/index.html")


@app.post("/send-greeting")
async def send_greeting(session_id:str = Form(default="1"), topic:str =Form(default="general")):
   text = f"Hello! I am your intake assistant for {topic}. How can I help you today?"
   greeting = await start_speech(text)
   SESSION_HISTORY[session_id].append({"role": "assistant", "content": text})
   return {"audio64": greeting}
   


@app.post("/voice-chat")
async def send_speech(audio: UploadFile = File(...), topic: str = Form(default="general"), session_id: str = Form(default="1")):
    audio_bytes = await audio.read()

    response = run_pipeline(audio_bytes=audio_bytes, topic=topic, session_id=session_id)
    return StreamingResponse(
        content=response,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )