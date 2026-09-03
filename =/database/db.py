"""Small SQLite persistence layer for profiles, materials, quizzes, and plans."""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "mentor.db"

def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, subject TEXT, level TEXT, study_hours REAL, exam_date TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, filename TEXT UNIQUE, course TEXT, topic TEXT, pages INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS quiz_results (id INTEGER PRIMARY KEY, student_id INTEGER, score INTEGER, total INTEGER, percentage REAL, topic_scores TEXT, mistakes TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY, quiz_id INTEGER, question TEXT, answer TEXT, topic TEXT, difficulty TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS study_plans (id INTEGER PRIMARY KEY, student_id INTEGER, plan TEXT, created_at TEXT);
        """)

def save_student(profile: dict[str, Any]) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as db:
        db.execute("INSERT INTO students (id,name,subject,level,study_hours,exam_date,updated_at) VALUES (1,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,subject=excluded.subject,level=excluded.level,study_hours=excluded.study_hours,exam_date=excluded.exam_date,updated_at=excluded.updated_at", (profile["name"], profile["subject"], profile["level"], profile["study_hours"], profile["exam_date"], now))
    return 1

def get_student() -> dict[str, Any] | None:
    with connect() as db:
        row = db.execute("SELECT * FROM students WHERE id=1").fetchone()
    return dict(row) if row else None

def add_document(filename: str, course: str, topic: str = "General", pages: int = 0) -> bool:
    with connect() as db:
        cursor = db.execute("INSERT OR IGNORE INTO documents (filename,course,topic,pages,created_at) VALUES (?,?,?,?,?)", (filename, course, topic, pages, datetime.now().isoformat(timespec="seconds")))
    return cursor.rowcount > 0

def list_documents() -> list[dict[str, Any]]:
    with connect() as db: rows = db.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]

def save_quiz_result(student_id: int, score: int, total: int, topic_scores: dict, mistakes: list) -> None:
    with connect() as db:
        quiz = db.execute("INSERT INTO quiz_results (student_id,score,total,percentage,topic_scores,mistakes,created_at) VALUES (?,?,?,?,?,?,?)", (student_id, score, total, score / total * 100 if total else 0, json.dumps(topic_scores), json.dumps(mistakes), datetime.now().isoformat(timespec="seconds")))
        quiz_id = quiz.lastrowid
        for mistake in mistakes:
            db.execute("INSERT INTO questions (quiz_id,question,answer,topic,difficulty,created_at) VALUES (?,?,?,?,?,?)", (quiz_id, mistake.get("question", ""), mistake.get("answer", ""), mistake.get("topic", "General"), mistake.get("difficulty", "Medium"), datetime.now().isoformat(timespec="seconds")))

def get_quiz_results() -> list[dict[str, Any]]:
    with connect() as db: rows = db.execute("SELECT * FROM quiz_results ORDER BY created_at DESC").fetchall()
    results = []
    for row in rows:
        item = dict(row); item["topic_scores"] = json.loads(item["topic_scores"] or "{}"); item["mistakes"] = json.loads(item["mistakes"] or "[]"); results.append(item)
    return results

def save_plan(student_id: int, plan: list[dict]) -> None:
    with connect() as db: db.execute("INSERT INTO study_plans (student_id,plan,created_at) VALUES (?,?,?)", (student_id, json.dumps(plan), datetime.now().isoformat(timespec="seconds")))

def get_latest_plan(student_id: int = 1) -> list[dict] | None:
    with connect() as db: row = db.execute("SELECT plan FROM study_plans WHERE student_id=? ORDER BY created_at DESC LIMIT 1", (student_id,)).fetchone()
    return json.loads(row["plan"]) if row else None
