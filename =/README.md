# GenAI Learning Mentor

GenAI Learning Mentor is a simple, AI-powered study companion built for a college project. Students upload course notes, ask grounded questions, practice with adaptive quizzes, track weak areas, and receive a realistic study plan.

## Problem statement
Students often have notes, assessments, and deadlines but no personalized feedback loop. This project combines retrieval-augmented generation, quiz analytics, and a lightweight learning coach in one understandable application.

## Features
- Student profile with course, level, study hours, and exam date
- PDF/TXT extraction, cleaning, chunking, and ChromaDB indexing
- RAG-based tutor with source/page display
- Multiple-choice, true/false, and short-answer quiz generation
- Quiz scoring, explanations, topic-level analytics, and SQLite history
- Strong, moderate, and weak topic classification
- Personalized study plan with weak-topic priority and revision
- Practice mode and learning coach
- 3D learning-orbit visualization on the dashboard
- Chronological activity timeline for indexed notes and quiz attempts
- Study-atmosphere image gallery using remote image assets
- Friendly handling of missing keys, empty files, invalid files, and API failures

## Architecture
```text
Streamlit UI (app.py)
    |-- profile, pages, session state
    |-- SQLite (database/db.py)
    |-- Document loader -> ChromaDB (rag/)
    `-- Mentor services (mentor/)
            `-- OpenAI chat + embeddings
```

## Technologies
Python 3.11+, Streamlit, OpenAI API, ChromaDB, PyPDF, SQLite, pandas, and python-dotenv.

## Installation

```powershell
cd "c:\Users\Bharat Negi\OneDrive\Desktop\projects\="
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and set `OPENAI_API_KEY`. `OPENAI_MODEL` defaults to `gpt-4o-mini`. The API key is never stored in source code.

## Run

```powershell
streamlit run app.py
```

Open the local URL shown by Streamlit, create a profile, upload a PDF/TXT, and use the Tutor or Quiz pages.

## How RAG works
1. PyPDF extracts PDF pages (or UTF-8 text is read from TXT files).
2. Text is normalized and split into overlapping chunks.
3. OpenAI `text-embedding-3-small` creates vectors.
4. ChromaDB stores vectors, text, filename, course, topic, and page metadata.
5. A question is embedded and the closest chunks are retrieved.
6. Retrieved context is sent to the tutor with a grounded system prompt, and sources are shown below the response.

## Adaptive tutoring
The profile level and quiz results are included in mentor prompts. Progress is classified as strong (80-100%), moderate (60-79%), or weak (below 60%). The coach and study plan prioritize weak topics while retaining strong-topic revision.

## Weak-area detection
Each quiz stores topic scores and mistakes in SQLite. The analyzer averages historical topic scores and chooses the lowest weak topic as the priority. This keeps the logic transparent and easy to explain.

## AI learning coach
The coach receives the profile, recent quiz history, and weak topics. Its practical tools are represented by the same separated services used by the UI: material retrieval, progress analysis, quiz generation, study-plan creation, and practice generation. This avoids a complex agent framework while keeping responsibilities clear.

## Example screenshots
Add screenshots of the Dashboard, Course Materials, AI Tutor, Quiz, Progress, Study Plan, Practice, and Learning Coach pages here after running the app.

## Testing checklist
- Start without an API key and confirm friendly messages appear.
- Upload an empty or unsupported file.
- Upload the same document twice.
- Create a profile and verify `data/mentor.db` is created.
- Generate and submit a quiz; verify score and mistakes.
- Complete two quizzes with different topics and inspect Progress.
- Set an exam date within two weeks and build a Study Plan.

## Future improvements
Authentication, per-user vector collections, streaming responses, richer misconception tracking, calendar export, offline embeddings, and automated UI tests could be added later.
