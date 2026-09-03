"""Progress aggregation and weak-area recommendations."""
def analyze_progress(results: list[dict]) -> dict:
    topic_values: dict[str, list[float]] = {}
    for result in results:
        for topic, score in result.get("topic_scores", {}).items(): topic_values.setdefault(topic, []).append(float(score))
    topics = {topic: round(sum(values) / len(values)) for topic, values in topic_values.items()}
    strong = {topic: score for topic, score in topics.items() if score >= 80}; moderate = {topic: score for topic, score in topics.items() if 60 <= score < 80}; weak = {topic: score for topic, score in topics.items() if score < 60}
    return {"topics": topics, "strong": strong, "moderate": moderate, "weak": weak, "priority": min(weak, key=weak.get) if weak else (min(moderate, key=moderate.get) if moderate else None)}
