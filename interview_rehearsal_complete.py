import streamlit as st
import anthropic
import os
from datetime import datetime

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="AI 면접 리허설",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================== 스타일 (차분한 긴장감) ====================
st.markdown("""
<style>
    /* 전체 배경 - 딥 네이비 */
    .stApp {
        background: linear-gradient(135deg, #1a1d29 0%, #2d3748 100%);
    }
    
    /* 메인 타이틀 */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #e2e8f0;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    /* 서브 타이틀 */
    .sub-title {
        font-size: 1.1rem;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    
    /* 질문 카드 */
    .question-card {
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #3b82f6;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    /* 압박 질문 카드 */
    .pressure-question {
        background: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #ef4444;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* 응원 메시지 */
    .encouragement {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    /* 버튼 스타일 */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ==================== Claude API 설정 ====================
# Streamlit Cloud와 로컬 환경 둘 다 지원
try:
    # Streamlit Cloud용 (secrets.toml)
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
except:
    # 로컬 환경변수용 (.env)
    api_key = os.environ.get("ANTHROPIC_API_KEY")

# API 키 검증
if not api_key:
    st.error("🔑 ANTHROPIC_API_KEY가 설정되지 않았습니다!")
    st.info("""
    **로컬 실행 시:**
    1. `.env.example`을 `.env`로 복사
    2. `.env` 파일에 실제 API 키 입력
    3. `export ANTHROPIC_API_KEY="your_key"` 또는 `.env` 파일 사용
    
    **Streamlit Cloud 배포 시:**
    1. 앱 페이지 우측 하단 "Manage app" 클릭
    2. Settings → Secrets 탭
    3. 아래 내용 입력 후 저장:
    ```
    ANTHROPIC_API_KEY = "your_actual_api_key_here"
    ```
    """)
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# ==================== 질문 리스트 (라이라 기획안) ====================
QUESTIONS = [
    {"q": "30초로 자기소개 해볼까요?", "pressure": False},
    {"q": "이직 사유를 솔직하게 말씀해주세요.", "pressure": False},
    {"q": "가장 자신 있는 성과를 숫자로 말씀해주세요.", "pressure": False},
    {"q": "그 성과에서 본인 기여는 정확히 뭐였나요?", "pressure": False},
    {"q": "가장 힘들었던 실패 경험은? 그리고 어떻게 수습했나요?", "pressure": False, "special": "failure"},
    {"q": "갈등 상황에서 본인 스타일은? 실제 사례로 말씀해주세요.", "pressure": False},
    {"q": "우리 회사 지원 이유가 연봉/거리 말고 뭔가요?", "pressure": False},
    {"q": "본인 약점 1개와 최근 3개월 개선 행동은?", "pressure": True},
    {"q": "입사하면 30일 안에 뭘 하실 건가요?", "pressure": True},
    {"q": "마지막으로 질문 있으신가요?", "pressure": False}
]

# ==================== 시스템 프롬프트 ====================
SYSTEM_PROMPT = """You are a warm, supportive interview coach conducting realistic job interview practice.

🎯 YOUR ROLE:
- Provide feedback on user's answer ONLY
- Do NOT ask the next question (the app will do that)
- Be encouraging but honest
- Help them speak concisely (20-30 seconds is ideal)

📋 FEEDBACK FORMAT (MANDATORY - ALWAYS USE THIS EXACT STRUCTURE):

**✅ 잘한 점:**
[1 sentence about what worked]

**🤖 AI 티 / 모호한 표현:**
[1 sentence pointing out generic or AI-like phrases]

**💡 개선 포인트:**
[1 specific improvement suggestion]

**✨ 예시 답변 (당신 말투로):**
[2-3 sentences showing better version in their style]

⚠️ CRITICAL RULES:
- NEVER provide answers before they speak
- NEVER be harsh or discouraging
- ALWAYS use the 4-part format above
- Keep total feedback under 150 words
- End with encouragement, NOT a question

🎤 20-30 SECOND COACHING:
If answer is too long (>50 words), gently remind:
"면접에서는 30초 안에 핵심만 전달하는 게 좋아요. 조금 더 간결하게 다시 해볼까요?"
"""

# 5번 질문 특별 분석 프롬프트
FAILURE_ANALYSIS_PROMPT = """Analyze this answer to the failure question.

Check if the answer has:
1. Emotional words (당황, 불안, 책임감, etc.)
2. Personal accountability (not blaming others)
3. Specific feelings (not just results)

Respond ONLY with:
- "NEEDS_EMOTION" if answer is abstract/generic/lacks emotion
- "OK" if answer includes genuine emotion and personal reflection

Answer to analyze: {answer}

Your assessment:"""

# ==================== 세션 상태 초기화 ====================
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'question_count' not in st.session_state:
    st.session_state.question_count = 0
if 'mode' not in st.session_state:
    st.session_state.mode = 'free'
if 'awaiting_emotion_answer' not in st.session_state:
    st.session_state.awaiting_emotion_answer = False
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False

# ==================== 헬퍼 함수 ====================
def add_question_to_chat(question_num):
    """질문을 채팅에 추가"""
    if question_num >= len(QUESTIONS):
        return False
    
    q_data = QUESTIONS[question_num]
    q_text = q_data["q"]
    is_pressure = q_data.get("pressure", False)
    
    if is_pressure:
        message = f"""
        <div class='pressure-question'>
        <strong>🔥 압박 질문 {question_num + 1}</strong><br>
        {q_text}
        </div>
        """
    else:
        message = f"""
        <div class='question-card'>
        <strong>질문 {question_num + 1}</strong><br>
        {q_text}
        </div>
        """
    
    st.session_state.messages.append({
        "role": "assistant", 
        "content": message,
        "is_question": True
    })
    return True

def add_emotion_question():
    """감정 추가 질문"""
    message = """
    <div class='question-card' style='border-left-color: #f59e0b;'>
    <strong>💭 추가 질문</strong><br>
    그때 결과 말고요.<br>
    당시 당신이 실제로 느꼈던 감정은 뭐였나요?<br>
    <small style='color: #94a3b8;'>(당황, 불안, 억울함, 책임감… 솔직하게 말해도 괜찮아요)</small>
    </div>
    """
    st.session_state.messages.append({
        "role": "assistant",
        "content": message,
        "is_question": True
    })
    st.session_state.awaiting_emotion_answer = True

def get_claude_feedback(user_message):
    """Claude로부터 피드백 받기"""
    messages_for_api = []
    
    # 실제 대화 내용만 API에 전송 (질문 카드는 제외)
    for msg in st.session_state.messages:
        if not msg.get("is_question", False):
            messages_for_api.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # 현재 사용자 메시지 추가
    messages_for_api.append({
        "role": "user",
        "content": user_message
    })
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=messages_for_api
        )
        return response.content[0].text
    except Exception as e:
        return f"❌ 오류가 발생했습니다: {str(e)}\n\n💡 ANTHROPIC_API_KEY를 확인해주세요."

def analyze_failure_answer(answer):
    """실패 질문 답변 분석"""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": FAILURE_ANALYSIS_PROMPT.format(answer=answer)
            }]
        )
        result = response.content[0].text.strip()
        return "NEEDS_EMOTION" in result
    except:
        return False

# ==================== 메인 화면 ====================
# 헤더
st.markdown("<div class='main-title'>🎯 AI 면접 리허설</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>면접 답을 만들어주지 않습니다.<br>말하는 연습을 함께합니다.</div>", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    
    mode_label = st.radio(
        "모드 선택",
        ["🆓 무료 체험 (3문항)", "💼 실전 라운드 (10문항)"],
        index=0 if st.session_state.mode == 'free' else 1
    )
    st.session_state.mode = 'free' if '무료' in mode_label else 'paid'
    
    st.divider()
    
    # 진행 상황
    if st.session_state.interview_started:
        max_q = 3 if st.session_state.mode == 'free' else 10
        progress = min(st.session_state.question_count, max_q) / max_q
        st.progress(progress)
        st.caption(f"진행: {min(st.session_state.question_count, max_q)}/{max_q} 문항")
    
    st.divider()
    
    if st.button("🔄 새로 시작", use_container_width=True):
        st.session_state.messages = []
        st.session_state.question_count = 0
        st.session_state.awaiting_emotion_answer = False
        st.session_state.interview_started = False
        st.rerun()

# ==================== 시작 버튼 ====================
if not st.session_state.interview_started:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎤 7분 무료 리허설 시작", use_container_width=True, type="primary"):
            st.session_state.interview_started = True
            add_question_to_chat(0)
            st.session_state.question_count = 1
            st.rerun()
    
    st.stop()

# ==================== 채팅 인터페이스 ====================
# 채팅 히스토리 표시
for msg in st.session_state.messages:
    if msg.get("is_question", False):
        # 질문 카드는 HTML로 직접 렌더링
        st.markdown(msg["content"], unsafe_allow_html=True)
    else:
        # 일반 메시지
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ==================== 무료 모드 3문항 제한 ====================
if st.session_state.mode == 'free' and st.session_state.question_count > 3:
    st.markdown("""
    <div class='encouragement'>
        <h3 style='margin-top: 0;'>당신의 말에는 이미 진심이 있어요 💙</h3>
        <p style='font-size: 1.1rem; margin: 1.5rem 0;'>
            지금은 다만, 그 진심을 조금 더 또렷하게 만드는 단계예요.<br>
            실전에서는 조금 더 날카로운 질문이 들어옵니다.
        </p>
        <p style='font-size: 0.95rem; color: #e2e8f0; margin-bottom: 1.5rem;'>
            한 번 더 함께 연습해볼까요?
        </p>
        <div style='background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; margin-top: 1rem;'>
            <strong>💼 실전 라운드</strong><br>
            10문항 + 압박 질문 2개 포함<br>
            <strong style='font-size: 1.3rem;'>₩4,900</strong>
        </div>
        <br>
        <button style='background: white; color: #667eea; border: none; padding: 1rem 2rem; border-radius: 8px; font-weight: 700; cursor: pointer;'>
            실전 라운드로 함께 가기
        </button>
        <p style='font-size: 0.85rem; color: #cbd5e1; margin-top: 1rem;'>
            💡 결제 링크 준비 중입니다
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ==================== 사용자 입력 ====================
if prompt := st.chat_input("답변을 입력하세요... (20-30초 분량으로)"):
    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # ==================== 5번 질문 특별 처리 ====================
    # 5번 질문에 대한 첫 답변인 경우
    if (st.session_state.question_count == 5 and 
        not st.session_state.awaiting_emotion_answer and
        len([m for m in st.session_state.messages if m["role"] == "user"]) == 5):
        
        # 답변 분석
        needs_emotion = analyze_failure_answer(prompt)
        
        if needs_emotion:
            # 피드백 먼저 주기
            with st.chat_message("assistant"):
                with st.spinner("답변 분석 중..."):
                    feedback = get_claude_feedback(prompt)
                    st.markdown(feedback)
                    st.session_state.messages.append({"role": "assistant", "content": feedback})
            
            # 감정 질문 추가
            add_emotion_question()
            st.rerun()
        else:
            # 정상 피드백
            with st.chat_message("assistant"):
                with st.spinner("피드백 준비 중..."):
                    feedback = get_claude_feedback(prompt)
                    st.markdown(feedback)
                    st.session_state.messages.append({"role": "assistant", "content": feedback})
            
            # 다음 질문으로
            if st.session_state.mode == 'paid':
                add_question_to_chat(st.session_state.question_count)
                st.session_state.question_count += 1
                st.rerun()
    
    # 감정 추가 질문에 대한 답변인 경우
    elif st.session_state.awaiting_emotion_answer:
        with st.chat_message("assistant"):
            with st.spinner("피드백 준비 중..."):
                feedback = get_claude_feedback(prompt)
                st.markdown(feedback)
                st.session_state.messages.append({"role": "assistant", "content": feedback})
        
        st.session_state.awaiting_emotion_answer = False
        
        # 다음 질문으로
        if st.session_state.mode == 'paid':
            add_question_to_chat(st.session_state.question_count)
            st.session_state.question_count += 1
            st.rerun()
    
    # 일반 답변 처리
    else:
        with st.chat_message("assistant"):
            with st.spinner("피드백 준비 중..."):
                feedback = get_claude_feedback(prompt)
                st.markdown(feedback)
                st.session_state.messages.append({"role": "assistant", "content": feedback})
        
        # 다음 질문 추가
        max_questions = 3 if st.session_state.mode == 'free' else 10
        
        if st.session_state.question_count < max_questions:
            add_question_to_chat(st.session_state.question_count)
            st.session_state.question_count += 1
            st.rerun()
        else:
            # 종료
            if st.session_state.mode == 'paid':
                st.markdown("""
                <div class='encouragement'>
                    <h3>🎉 리허설 완료!</h3>
                    <p>실전 면접에서 좋은 결과 있으시길 응원합니다.</p>
                </div>
                """, unsafe_allow_html=True)
