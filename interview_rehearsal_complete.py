import os
import streamlit as st
from groq import Groq

# =========================
# Config
# =========================
st.set_page_config(page_title="Interview Rehearsal MVP", page_icon="🎤", layout="centered")

def load_groq_key() -> str | None:
    # Streamlit Cloud: st.secrets
    # Local: env var
    return st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

GROQ_API_KEY = load_groq_key()
if not GROQ_API_KEY:
    st.error("🔑 GROQ_API_KEY가 설정되지 않았습니다. (Streamlit Secrets 또는 환경변수 확인)")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# =========================
# UI Theme (simple & readable)
# =========================
st.markdown(
    """
<style>
.block-container {max-width: 760px;}
h1, h2, h3 {letter-spacing: -0.3px;}
.small-note {color: #7a7a7a; font-size: 0.9rem;}
.card {border: 1px solid rgba(0,0,0,0.08); border-radius: 14px; padding: 14px 14px; margin: 10px 0;}
.badge {display:inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.85rem; border: 1px solid rgba(0,0,0,0.12); margin-right: 6px;}
.hr {height: 1px; background: rgba(0,0,0,0.08); margin: 16px 0;}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# Interview content
# =========================
FREE_QUESTIONS = [
    "30초 자기소개 해볼까요?",
    "이직/지원 이유를 한 문장으로 먼저 말해볼래요?",
    "가장 자신 있는 성과 1개를 숫자와 함께 말해볼래요?",
]

PAID_QUESTIONS = [
    "30초 자기소개 해볼까요?",
    "이직/지원 이유를 ‘솔직하지만 안전하게’ 말해볼래요?",
    "가장 자신 있는 성과 1개를 숫자와 함께 말해볼래요?",
    "그 성과에서 본인 기여가 정확히 뭐였죠? (팀 덕 말고 ‘내 행동’ 중심)",
    "실패 경험 1개를 말해볼래요. 그리고 어떻게 수습했나요?",
    "그때 ‘솔직한 감정’은 뭐였나요? (당황/불안/억울/책임감 등 괜찮아요)",
    "갈등 상황에서 본인 스타일은 어떤가요? 실제 사례로.",
    "지원한 이유가 ‘연봉/거리’ 말고 뭐예요? (회사/직무의 포인트 1개)",
    "약점 1개와 최근 3개월 개선 행동을 말해볼래요?",
    "입사 후 30일 안에 뭘 하겠습니까? (짧게 3개)",
    "마지막으로 질문 있나요? (면접관에게 물을 질문 2개)",
    "압박 질문: 방금 말한 건 누구나 할 수 있는 얘기 아닌가요? 차별점이 뭐죠?",
]

UPSELL_COPY = (
    "여기까지는 워밍업이었어요.\n\n"
    "당신의 말에는 이미 **진심**이 있어요. 지금은 그 진심을 **조금 더 또렷하게 만드는 단계**예요.\n\n"
    "실전 라운드로 넘어가서(압박 질문 포함) 한 번 더 다듬어 볼까요?"
)

SYSTEM_PROMPT = """You are a realistic interview coach and interviewer.
Goal: simulate a real interview and help the user practice speaking.
Rules:
- Ask ONE question at a time.
- After the user answers, provide feedback in EXACTLY 4 bullet points:
  1) What worked (one sentence)
  2) What sounded generic/AI-like (one sentence)
  3) One improvement (one sentence)
  4) A rewritten example in the user's style (2-3 sentences max)
- Warm, respectful, horizontal partner tone. No harsh scoring.
- If answer is too long, suggest compressing to 20-30 seconds.
- If answer is too vague, ask ONE follow-up question before moving on.
- Do not mention policies or being an AI.
"""

def llm_feedback(question: str, answer: str, context: dict) -> str:
    # context can include mode, job, company_type, etc.
    user_msg = f"""Interview context:
- Mode: {context.get('mode')}
- Job/Role: {context.get('job')}
- Company type: {context.get('company_type')}

Question:
{question}

User answer:
{answer}

Now provide the 4-bullet feedback exactly as specified.
"""
    resp = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.6,
        max_tokens=420,
    )
    return resp.choices[0].message.content.strip()

def is_vague_failure(answer: str) -> bool:
    # super-light heuristic to trigger deeper probe
    a = (answer or "").strip().lower()
    if len(a) < 40:
        return True
    vague_markers = ["열심히", "노력", "최선을", "기억", "그냥", "대충", "많이", "좋았", "나쁘", "배웠"]
    return any(v in a for v in vague_markers)

# =========================
# Session State
# =========================
if "stage" not in st.session_state:
    st.session_state.stage = "home"  # home | run
if "mode" not in st.session_state:
    st.session_state.mode = "Free"   # Free | Pro
if "job" not in st.session_state:
    st.session_state.job = "기획/PM"
if "company_type" not in st.session_state:
    st.session_state.company_type = "일반"
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: {q, a, fb}
if "pending_followup" not in st.session_state:
    st.session_state.pending_followup = None  # if we ask follow-up before next

# =========================
# Home
# =========================
st.title("🎤 AI 면접 리허설")
st.markdown('<div class="small-note">정답을 만들어주지 않습니다. <b>말하는 연습</b>을 함께합니다.</div>', unsafe_allow_html=True)
st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

if st.session_state.stage == "home":
    st.markdown("### 설정")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.mode = st.selectbox("모드", ["Free", "Pro"], index=0, help="Free: 3문항 / Pro: 10+문항 + 압박 질문")
    with col2:
        st.session_state.company_type = st.selectbox("회사 성향", ["보수적", "일반", "스타트업"], index=1)

    st.session_state.job = st.selectbox("직무", ["기획/PM", "마케팅", "영업", "개발", "디자인", "생산/품질", "기타"], index=0)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**진행 방식**")
    st.write("- 질문 1개 → 답변 → 4줄 피드백 → 다음 질문")
    st.write(" ")
