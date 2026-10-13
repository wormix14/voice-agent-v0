from config import openai_client
from db.models import ReportORM
from db.session import SessionLocal
import asyncio

def extract_transcription(history: list[dict]) -> str:
  lines = []
  for item in history:
    role = item.get("role")
    content = item.get("content")

    if role in ("user", "assistant") and content:
      lines.append(f"{role}: {content}")

  return "\n".join(lines)


async def generate_summary(transcription: str, topic: str) -> str:
    response = await openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": (
          f"""You are an objective conversation summarizer.
          Your goal is to extract key facts and outcomes from a dialogue on the topic: "{topic}".

          Rules:
          - Write the entire summary — INCLUDING all field headers/labels — strictly in conversation language.
          - Do NOT use English headers if the conversation was in German, Polish, etc.
          - If information for a section is missing or unclear, write the equivalent of "Not specified" in the detected language.
          - Be concise, factual, and strictly grounded in the conversation without introductory remarks or conclusions.

          Output strictly following this template (translate the bracketed labels to the conversation language):
          [Topic]: <concise domain/intent, e.g. {topic}>
          [Main Objective]: <what the user wanted to achieve or resolve>
          [Key Details]: <bullet points or comma-separated list of critical data>
          [Outcome / Next Steps]: <status reached, solution provided, or action items>
          [Pending Issues]: <unresolved questions or 'None' in the target language>""")},
        {"role": "user", "content": transcription}
    ],
    
    temperature=0.2
    )
    return response.choices[0].message.content

def save_to_db(transcription: str, summary: str) -> None:
  with SessionLocal() as db_session:
    db_session.add(
        ReportORM(
            transcription=transcription,
            summary=summary,
        )
    )
    db_session.commit()

async def process_and_save(transcription: str, topic: str) -> None:
  summary = await generate_summary(transcription, topic)
  await asyncio.to_thread(save_to_db, transcription, summary)