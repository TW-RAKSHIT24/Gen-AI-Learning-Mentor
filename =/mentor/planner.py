"""Personalized plan generation with a deterministic fallback."""
from datetime import date, timedelta

def create_plan(profile: dict, weak: list[str], strong: list[str], days: int = 14) -> list[dict]:
    exam = date.fromisoformat(str(profile["exam_date"]))
    days = max(1, min(days, (exam - date.today()).days + 1))
    plan = []
    topics = weak + strong or [profile.get("subject", "Core concepts")]
    for index in range(days):
        is_mock_test = index == days - 1 and days > 1
        topic = "Mock test" if is_mock_test else topics[index % len(topics)]
        plan.append({"date": str(date.today() + timedelta(days=index)), "topic": topic, "duration": f"{profile.get('study_hours', 1)} hours", "learning_activity": f"Review notes and explain {topic} in your own words.", "practice_activity": f"Complete targeted practice on {topic}.", "revision_activity": "Recall yesterday's key ideas for 10 minutes.", "difficulty": "Focused" if topic in weak else "Review"})
    return plan
