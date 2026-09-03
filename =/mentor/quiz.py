"""Quiz and practice question generation."""
import json
from .tutor import ask_ai

def generate_questions(context: str, topic: str, difficulty: str, count: int, question_type: str = "Multiple choice") -> list[dict]:
    prompt = f"Return ONLY a JSON array of {count} objects with keys question, options, answer, explanation, topic, difficulty. Type: {question_type}. Topic: {topic}. Difficulty: {difficulty}. Use this source: {context or 'general course knowledge'}"
    try:
        text = ask_ai("You create accurate educational quiz questions. Keep answers grounded in the source when supplied.", prompt)
        start, end = text.find("["), text.rfind("]")
        return json.loads(text[start:end + 1]) if start >= 0 else []
    except (ValueError, json.JSONDecodeError): return []

def evaluate_questions(questions: list[dict], answers: dict) -> tuple[int, dict, list]:
    score = 0; topics: dict[str, list[int]] = {}; mistakes = []
    for index, question in enumerate(questions):
        expected = str(question.get("answer", "")).strip().lower(); actual = str(answers.get(str(index), "")).strip().lower()
        correct = int(actual == expected); score += correct
        topics.setdefault(question.get("topic", "General"), []).append(correct)
        if not correct: mistakes.append({"question": question.get("question", ""), "answer": question.get("answer", ""), "topic": question.get("topic", "General"), "difficulty": question.get("difficulty", "Medium"), "explanation": question.get("explanation", "")})
    return score, {topic: round(sum(values) / len(values) * 100) for topic, values in topics.items()}, mistakes
