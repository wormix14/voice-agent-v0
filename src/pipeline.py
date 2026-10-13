from services import transcribe_audio, generate_answer, start_speech
import json
import re
from collections import defaultdict
import logging
from tools import process_and_save, extract_transcription
import asyncio

logger = logging.getLogger(__name__)
SESSION_HISTORY: dict[str, list[dict]] = defaultdict(list)

def sse_event(event_type:str, payload: dict):
    data = {"type": event_type, **payload}
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def run_pipeline(audio_bytes: bytes, topic: str, session_id: str):
    sentence_delimiter = re.compile(r'([.!?\n]+)')
    buff=""
    sentence_index = 0
    history = SESSION_HISTORY[session_id]
    assistant_responses = []
    session_finished = False

    try:
        input_text = await transcribe_audio(audio_bytes=audio_bytes)
    except Exception as e:
        logger.exception(f"Deepgram exception: {e}")
        yield sse_event("done", {"session_finished": False})

    if not input_text:
        yield sse_event("error", {"message": "Unable to process speech"})
        yield sse_event("done", {"session_finished": False})
        return

    history.append({"role": "user", "content": input_text})

    yield sse_event(event_type="transcription", payload={"user_text": input_text})
    try:
        async for token in generate_answer(history=history, topic=topic):
            yield sse_event(event_type="text_delta", payload={"token": token})
            buff+=token
            if "[SESSION_FINISHED]" in buff:
                session_finished = True
                buff = buff.replace("[SESSION_FINISHED]", "")

            if "[" in buff and "]" not in buff:
                continue

            parts = sentence_delimiter.split(buff)
            if len(parts) > 2:
                full_part = (parts[0] + parts[1]).strip()
                buff = "".join(parts[2:])
                full_part = full_part.replace("[SESSION_FINISHED]", "").strip()
                
                if full_part:
                    assistant_responses.append(full_part)

                    audio = await start_speech(input_token=full_part)
                    yield sse_event(event_type="audio_delta", payload={
                        "index": sentence_index,
                        "text": full_part,
                        "audio64": audio}
                        )
                    sentence_index+=1

        
        remaining_sentence = buff.replace("[SESSION_FINISHED]", "").strip()
        if remaining_sentence and re.search(r'\w', remaining_sentence):
            assistant_responses.append(remaining_sentence)
            audio64 = await start_speech(input_token=remaining_sentence)
            yield sse_event("audio_delta", payload={
            "index": sentence_index,
            "text": remaining_sentence,
            "audio64": audio64,
                }
            )
    except Exception as e:
        logger.exception("Error in speech generation")
    finally:
        full_bot_text = " ".join(assistant_responses).strip()
        if full_bot_text:
            history.append({"role": "assistant", "content": full_bot_text})
            if session_finished:
                transcription = extract_transcription(history=history)
                asyncio.create_task(process_and_save(transcription=transcription, topic=topic))
                SESSION_HISTORY.pop(session_id, None)
                        
        yield sse_event(event_type="done", payload={"session_finished": session_finished})
        