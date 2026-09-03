"""OpenAI-backed grounded tutor and learning coach."""
import json, os
from openai import OpenAI
from rag.retriever import retrieve_context

TUTOR_PROMPT = """You are a patient and adaptive AI learning mentor. Use the student's course material as the primary source. Do not invent unsupported facts; say when the material does not contain the answer. Adapt to {level}, explain step-by-step, use examples when useful, and ask one short understanding-check question. Course: {subject}."""

def ask_ai(system: str, user: str) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key: return "Add OPENAI_API_KEY to your .env file to enable the AI response."
    response = OpenAI(api_key=key).chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.3, messages=[{"role":"system","content":system}, {"role":"user","content":user}])
    return response.choices[0].message.content or "I could not generate a response."

def tutor_answer(question: str, profile: dict) -> tuple[str, list[dict]]:
    context, sources = retrieve_context(question)
    if not context: return ("I could not find relevant material. Upload course notes so I can give a grounded answer.", [])
    answer = ask_ai(TUTOR_PROMPT.format(level=profile.get("level", "Beginner"), subject=profile.get("subject", "your course")), f"Course context:\n{context}\n\nStudent question: {question}")
    return answer, sources

def coach_answer(request: str, profile: dict, weak: list[str], history: list[dict]) -> str:
    summary = ", ".join(weak) or "No weak topics identified yet"
    return ask_ai(f"You are a practical learning coach. Student level: {profile.get('level')}; exam: {profile.get('exam_date')}; daily hours: {profile.get('study_hours')}. Weak topics: {summary}. Give a prioritized, realistic next action.", f"Quiz history: {json.dumps(history[:5])}\nStudent request: {request}")
