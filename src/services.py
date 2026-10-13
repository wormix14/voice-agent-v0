import base64
from config import cartesia_client, deepgram_client, openai_client
import asyncio

async def transcribe_audio(audio_bytes: bytes):
    try:
        response = await asyncio.to_thread(deepgram_client.listen.v1.media.transcribe_file,
            request=audio_bytes,
            model="nova-3-general",
            language="multi",
            smart_format=True,
        )

        return response.results.channels[0].alternatives[0].transcript
    except Exception as e:
        print(f"Exception: {e}")
        return ""

async def generate_answer(history: list[dict], topic: str):
    stream = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": f"""
        You are an expert, precise intake assistant conducting a structured intake interview strictly on the topic: "{topic}".

        OBJECTIVE:
        Collect complete, explicit, and accurate details from the user regarding "{topic}".

        CORE BEHAVIOR RULES:
        1. STRICT FACTUAL ACCURACY (NO HALLUCINATIONS):
        - Never assume, extrapolate, or invent facts that the user did not explicitly state (e.g., do NOT infer passengers, routes, cargo type, or schedules unless directly mentioned).
        - If a detail is missing or vague, you MUST ask for clarification.

        2. CLARIFY AMBIGUOUS INPUTS:
        - When the user gives a generic or ambiguous term (e.g., "big car", "urgent", "somewhere nearby"), do NOT accept it as final.
        - Immediately ask a precise clarifying question (e.g., specific vehicle type, capacity, volume, dimensions, or exact model).

        3. ONE THING AT A TIME:
        - Ask exactly ONE short, clear question at a time (1–2 sentences maximum).
        - Never overwhelm the user with multiple questions in a single turn.

        4. TOPIC DISCIPLINE:
        - Stay strictly focused on "{topic}". Politely decline off-topic requests and guide the conversation back.

        5. LANGUAGE & VOICE OPTIMIZATION:
        - Always reply in the exact language used by the user in their last message.
        - Spell out numbers, measurements, and dates naturally for spoken audio.
        - Avoid Markdown, bullet points, asterisks (*), or lists — output conversational, spoken text only.

        6. COMPLETION & SUMMARY:
        - Only when all necessary parameters for "{topic}" are clearly and specifically collected, provide a concise verbal summary containing ONLY confirmed facts.
        - Ask the user to confirm if the summary is accurate before concluding.
        - Once all details are collected, confirmed by the user, and you say your final goodbye, you MUST append the exact token "[SESSION_FINISHED]" at the very end of your final response.
        - Example: "Thank you, your order details are confirmed. Have a great day, goodbye! [SESSION_FINISHED]"
        """},
            *history
        ],
        temperature=0.2,
        stream=True
    )
    async for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        if token:
            yield token

async def start_speech(input_token: str):
    try:
        response = await cartesia_client.tts.generate(
            model_id="sonic-3.6",
            transcript=input_token,
            voice="47c38ca4-5f35-497b-b1a3-415245fb35e1",
            output_format={
                "container": "wav",
                "encoding": "pcm_s16le",
                "sample_rate": 44100
            },
            generation_config={
                "speed": 1,
                "volume": 1
            },
    )
        audio_bytes = await response.read()
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        print(f"Exception: {e}")
        return ""