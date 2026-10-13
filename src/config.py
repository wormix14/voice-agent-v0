from cartesia import AsyncCartesia
from deepgram import DeepgramClient
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

load_dotenv(".env")

deepgram_client = DeepgramClient()
cartesia_client = AsyncCartesia(api_key=os.getenv("CARTESIA_API_KEY"))
openai_client = AsyncOpenAI()
