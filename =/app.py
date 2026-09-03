"""GenAI Learning Mentor - Streamlit application."""
from datetime import date
from html import escape
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from database.db import init_db, save_student, get_student, add_document, list_documents, save_quiz_result, get_quiz_results, save_plan, get_latest_plan
from mentor.analyzer import analyze_progress
from mentor.planner import create_plan
from mentor.quiz import generate_questions, evaluate_questions
from mentor.tutor import tutor_answer, coach_answer
from rag.document_loader import extract_text, chunk_pages
from rag.vector_store import VectorStore
from rag.retriever import retrieve_context

load_dotenv(); init_db()
st.set_page_config(page_title="GenAI Learning Mentor", page_icon="🎓", layout="wide")

CSS = """<style>
[data-testid='stMetric'] { background:#f4f7f6; border:1px solid #dfe8e4; padding:14px; border-radius:8px; }
.block-container { max-width: 1200px; padding-top: 2rem; }
.orbit-shell { background:linear-gradient(135deg,#102a43 0%,#1d4e89 55%,#0f766e 100%); border-radius:18px; min-height:280px; overflow:hidden; padding:24px; position:relative; color:#f4fbf9; }
.orbit-copy { position:relative; z-index:2; max-width:310px; }
.orbit-copy h3 { color:#d7fff2; margin:0 0 8px; font-size:1.15rem; }
.orbit-copy p { color:#c7e5df; font-size:.9rem; line-height:1.45; }
.orbit-scene { height:230px; perspective:700px; position:absolute; right:2%; top:24px; width:55%; }
.orbit-ring { border:1px solid rgba(212,255,243,.45); border-radius:50%; height:175px; left:18%; position:absolute; top:27px; transform:rotateX(65deg) rotateZ(-12deg); width:290px; }
.orbit-ring.second { height:125px; left:29%; top:52px; transform:rotateX(65deg) rotateZ(58deg); width:220px; }
.orbit-core { align-items:center; background:radial-gradient(circle at 35% 30%,#fef3c7,#f59e0b 42%,#b45309); border-radius:50%; box-shadow:0 0 38px rgba(251,191,36,.65); display:flex; height:72px; justify-content:center; left:43%; position:absolute; top:77px; width:72px; z-index:2; }
.orbit-core span { color:#542b05; font-size:1.5rem; }
.orbit-node { align-items:center; background:#f4fbf9; border:4px solid #7dd3c7; border-radius:50%; box-shadow:0 6px 18px rgba(0,0,0,.24); color:#102a43; display:flex; font-size:.7rem; font-weight:700; height:44px; justify-content:center; position:absolute; text-align:center; width:44px; z-index:3; }
.orbit-node.one { left:11%; top:44px; } .orbit-node.two { right:8%; top:18px; } .orbit-node.three { bottom:12px; left:26%; } .orbit-node.four { bottom:0; right:19%; }
.timeline { border-left:2px solid #a7d7ce; margin:8px 0 0 10px; padding-left:24px; }
.timeline-item { margin:0 0 18px; position:relative; }
.timeline-item:before { background:#0f766e; border:3px solid #e6fffa; border-radius:50%; box-shadow:0 0 0 1px #0f766e; content:''; height:10px; left:-31px; position:absolute; top:4px; width:10px; }
.timeline-date { color:#0f766e; font-size:.72rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }
.timeline-title { color:#102a43; font-weight:700; margin-top:2px; }
.timeline-detail { color:#526b7a; font-size:.82rem; margin-top:2px; }
</style>"""
st.markdown(CSS, unsafe_allow_html=True)

def render_learning_orbit(progress: dict, average: int, profile: dict):
        priority = escape(str(progress["priority"] or "Ready to explore"))
        level = escape(str(profile.get("level", "Beginner")))
        st.markdown(f"""
        <div class="orbit-shell">
            <div class="orbit-copy">
                <h3>Your learning orbit</h3>
                <p>{level} path · {average}% average</p>
                <p>Center today's momentum on <strong>{priority}</strong>. Each node represents a part of your study loop.</p>
            </div>
            <div class="orbit-scene" aria-label="3D learning orbit visualization">
                <div class="orbit-ring"></div><div class="orbit-ring second"></div>
                <div class="orbit-core"><span>{average}%</span></div>
                <div class="orbit-node one">NOTES</div><div class="orbit-node two">ASK</div>
                <div class="orbit-node three">QUIZ</div><div class="orbit-node four">REVIEW</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_activity_timeline(results: list[dict], documents: list[dict]):
        events = []
        for document in documents:
                events.append((document.get("created_at", ""), "Course material indexed", f"{document['filename']} · {document['topic']}"))
        for result in results:
                events.append((result.get("created_at", ""), "Quiz completed", f"{result['score']}/{result['total']} · {round(result['percentage'])}%"))
        events.sort(key=lambda event: event[0], reverse=True)
        if not events:
                st.caption("Your learning timeline will appear as you upload notes and complete quizzes.")
                return
        timeline = "<div class='timeline'>"
        for timestamp, title, detail in events[:8]:
                timeline += f"<div class='timeline-item'><div class='timeline-date'>{escape(timestamp.replace('T', ' ')[:16])}</div><div class='timeline-title'>{escape(title)}</div><div class='timeline-detail'>{escape(detail)}</div></div>"
        st.markdown(timeline + "</div>", unsafe_allow_html=True)

def profile_form() -> dict:
    current = get_student() or {"name": "", "subject": "", "level": "Beginner", "study_hours": 1.0, "exam_date": str(date.today())}
    with st.sidebar:
        st.title("🎓 Learning Mentor")
        st.caption("Your personal study companion")
        with st.form("profile"):
            name = st.text_input("Name", current.get("name", ""))
            subject = st.text_input("Subject / course", current.get("subject", ""))
            level = st.selectbox("Knowledge level", ["Beginner", "Intermediate", "Advanced"], index=["Beginner", "Intermediate", "Advanced"].index(current.get("level", "Beginner")))
            hours = st.number_input("Daily study hours", 0.5, 12.0, float(current.get("study_hours", 1.0)), 0.5)
            exam = st.date_input("Exam date", date.fromisoformat(str(current.get("exam_date", date.today()))))
            if st.form_submit_button("Save profile", type="primary"):
                save_student({"name": name or "Student", "subject": subject or "General studies", "level": level, "study_hours": hours, "exam_date": str(exam)})
                st.success("Profile saved."); st.rerun()
    return get_student() or {"name": "Student", "subject": "General studies", "level": "Beginner", "study_hours": 1, "exam_date": str(date.today())}

def page_dashboard(profile: dict):
    st.title(f"Good to see you, {profile['name']} 👋")
    results = get_quiz_results(); documents = list_documents(); progress = analyze_progress(results); days = max(0, (date.fromisoformat(profile["exam_date"]) - date.today()).days)
    st.caption(f"{profile['subject']} · {profile['level']} learner")
    cols = st.columns(4); average = round(sum(r["percentage"] for r in results) / len(results)) if results else 0
    cols[0].metric("Overall quiz score", f"{average}%"); cols[1].metric("Days to exam", days); cols[2].metric("Strong topics", len(progress["strong"])); cols[3].metric("Weak topics", len(progress["weak"]))
    render_learning_orbit(progress, average, profile)
    st.subheader("Today's focus")
    focus = progress["priority"] or "Upload course material"
    st.info(f"Spend {profile['study_hours']} hours on **{focus}**. Use the AI Tutor for a step-by-step explanation, then take a short quiz.")
    left, right = st.columns(2)
    with left:
        st.subheader("Topic health")
        if progress["topics"]: st.dataframe(pd.DataFrame([{"Topic": k, "Score": f"{v}%"} for k, v in progress["topics"].items()]), hide_index=True, use_container_width=True)
        else: st.caption("Complete a quiz to see topic performance.")
    with right:
        st.subheader("Recent activity")
        st.write(f"{len(results)} quiz attempt(s) recorded")
        st.progress(min(average / 100, 1.0), text="Average performance")
    timeline_col, gallery_col = st.columns([1, 1.35])
    with timeline_col:
        st.subheader("Learning timeline")
        render_activity_timeline(results, documents)
    with gallery_col:
        st.subheader("Study atmosphere")
        image_cols = st.columns(3)
        images = [
            ("https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=500&q=80", "Build your notes"),
            ("https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=500&q=80", "Focus block"),
            ("https://images.unsplash.com/photo-1456324504439-367cee3b3c32?w=500&q=80", "Reflect and review"),
        ]
        for image_col, (url, caption) in zip(image_cols, images):
            with image_col: st.image(url, caption=caption, width="stretch")

def page_materials(profile: dict):
    st.title("📚 Course Materials"); st.write("Upload notes once and use them across tutoring, quizzes, and planning.")
    upload = st.file_uploader("Choose a PDF or TXT file", type=["pdf", "txt"])
    topic = st.text_input("Topic label (optional)", "General")
    if upload and st.button("Index document", type="primary"):
        try:
            if not add_document(upload.name, profile["subject"], topic): st.warning("This document is already indexed.")
            else:
                chunks = chunk_pages(extract_text(upload)); count = VectorStore().add(chunks, upload.name, profile["subject"], topic)
                st.success(f"Document uploaded and indexed successfully. {count} chunks ready.")
        except Exception as error: st.error(f"Could not index this file: {error}")
    docs = list_documents()
    if docs: st.dataframe(pd.DataFrame(docs)[["filename", "course", "topic", "pages", "created_at"]], hide_index=True, use_container_width=True)

def page_tutor(profile: dict):
    st.title("💬 AI Tutor"); question = st.text_area("What would you like to understand?", placeholder="Explain recursion with a simple example...")
    if st.button("Ask mentor", type="primary"):
        if not question.strip(): st.warning("Enter a question first.")
        else:
            try:
                answer, sources = tutor_answer(question, profile); st.markdown(answer)
                if sources:
                    with st.expander("Retrieved course sources"):
                        for source in sources: st.caption(f"{source['metadata']['filename']} · page {source['metadata']['page']}"); st.write(source["text"])
            except Exception as error: st.error(f"The tutor is temporarily unavailable: {error}")

def page_quiz(profile: dict, practice: bool = False):
    st.title("💪 Practice" if practice else "📝 Quiz")
    docs = list_documents(); topics = sorted({d["topic"] for d in docs}) or ["General"]
    topic = st.selectbox("Topic", topics); difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Difficult"]); count = st.slider("Number of questions", 1, 10, 5)
    qtype = st.selectbox("Question type", ["Multiple choice", "True/False", "Short answer"]) if not practice else "Multiple choice"
    if st.button("Generate questions", type="primary"):
        try:
            context, _ = retrieve_context(topic, limit=8) if docs else ("", [])
            with st.spinner("Creating questions..."):
                st.session_state.quiz = generate_questions(context, topic, difficulty, count, qtype)
                st.session_state.quiz_requested = True
        except Exception as error:
            st.session_state.quiz = []
            st.session_state.quiz_requested = True
            st.error(f"Could not generate questions: {error}")
    questions = st.session_state.get("quiz", [])
    if st.session_state.get("quiz") == [] and st.session_state.get("quiz_requested"):
        st.warning("No questions were generated. Check your API key and try again.")
    if questions:
        with st.form("quiz_form"):
            answers = {}
            for index, question in enumerate(questions):
                st.markdown(f"**{index + 1}. {question.get('question', '')}**")
                options = question.get("options") or (["True", "False"] if qtype == "True/False" else None)
                answers[str(index)] = st.radio("Answer", options, key=f"answer_{index}") if options else st.text_input("Your answer", key=f"answer_{index}")
            if st.form_submit_button("Submit quiz"):
                score, topic_scores, mistakes = evaluate_questions(questions, answers); save_quiz_result(1, score, len(questions), topic_scores, mistakes)
                st.session_state.quiz_result = (score, len(questions), mistakes); st.rerun()
    if st.session_state.get("quiz_result"):
        score, total, mistakes = st.session_state.quiz_result; st.success(f"Your score: {score}/{total} ({round(score / total * 100)}%)")
        if mistakes:
            st.subheader("Review your mistakes")
            for mistake in mistakes: st.warning(f"{mistake['topic']}: {mistake['question']}\n\nAnswer: {mistake['answer']}\n\n{mistake['explanation']}")

def page_progress():
    st.title("📊 Progress"); results = get_quiz_results(); progress = analyze_progress(results)
    for label, key in [("Strong", "strong"), ("Moderate", "moderate"), ("Weak", "weak")]:
        st.subheader(label)
        values = progress[key]
        if values:
            for topic, score in values.items(): st.write(f"**{topic}** · {score}%"); st.progress(score / 100)
        else: st.caption("No topics here yet.")
    if progress["priority"]: st.info(f"Most important revision topic: **{progress['priority']}**")

def page_plan(profile: dict):
    st.title("🎯 Study Plan"); progress = analyze_progress(get_quiz_results()); days = max(1, (date.fromisoformat(profile["exam_date"]) - date.today()).days + 1)
    if st.button("Build personalized plan", type="primary"):
        plan = create_plan(profile, list(progress["weak"]), list(progress["strong"]), min(days, 14)); save_plan(1, plan); st.session_state.plan = plan
    plan = st.session_state.get("plan") or get_latest_plan()
    if plan: st.dataframe(pd.DataFrame(plan), hide_index=True, use_container_width=True)
    else: st.caption("Build a plan to prioritize weak topics and reserve time for revision.")

def page_coach(profile: dict):
    st.title("🤖 Learning Coach"); request = st.text_area("Tell the coach what you need", "I have an exam soon. What should I study next?")
    if st.button("Get recommendation", type="primary"):
        progress = analyze_progress(get_quiz_results())
        try: st.markdown(coach_answer(request, profile, list(progress["weak"]), get_quiz_results()))
        except Exception as error: st.error(f"The coach is temporarily unavailable: {error}")

profile = profile_form()
page = st.sidebar.radio("Navigate", ["🏠 Dashboard", "📚 Course Materials", "💬 AI Tutor", "📝 Quiz", "📊 Progress", "🎯 Study Plan", "💪 Practice", "🤖 Learning Coach"])
if page == "🏠 Dashboard": page_dashboard(profile)
elif page == "📚 Course Materials": page_materials(profile)
elif page == "💬 AI Tutor": page_tutor(profile)
elif page == "📝 Quiz": page_quiz(profile)
elif page == "📊 Progress": page_progress()
elif page == "🎯 Study Plan": page_plan(profile)
elif page == "💪 Practice": page_quiz(profile, True)
else: page_coach(profile)
