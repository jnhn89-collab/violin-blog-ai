import os
import google.generativeai as genai
from datetime import datetime

# ==========================================
# 1. 설정 (Setup)
# ==========================================

api_key = os.environ.get("GOOGLE_API_KEY")

# 블로그 설정 (대중 노출/정보성/홍보형)
STUDIO_NAME = "다산 라미 바이올린"
LOCATION = "남양주 다산신도시"
# VIBE: 친절하지만 핵심만 콕콕 짚어주는 정보통/해결사 느낌
TEACHER_VIBE = "에너지 넘치고 명쾌한, 꿀팁 대방출하는 다산신도시 정보통"

# ==========================================
# 2. '대중 노출형' 블로그 생성기 (Viral Prompt)
# ==========================================
def generate_viral_blog_post(topic, raw_notes):
    
    prompt = f"""
    당신은 {LOCATION}에서 활동하는 블로그 마케팅 전문가이자 '{TEACHER_VIBE}' 바이올린 선생님입니다.
    이번 글의 목적은 **'검색 노출'**과 **'대중적인 클릭 유도'**입니다. 바이올린을 잘 모르는 사람도 클릭하게 만들어야 합니다.
    
    [입력 소스]
    - 주제: {topic}
    - 선생님의 메모(재료): "{raw_notes}"

    [🔥 핵심 지령: 클릭을 부르는 정보성 글쓰기]
    1. **제목(Title) 전략**:
       - 호기심 자극: "절대 하지 마세요", "이것만 알면 끝"
       - 숫자 활용: "TOP 3", "5가지 방법", "3분 만에"
       - 타겟 명시: "다산맘 필독", "직장인 취미 추천"
       - *위 전략을 섞어 매력적인 제목 3가지를 먼저 제안하고, 그 중 하나로 글을 시작하세요.*
    
    2. **내용 구성 (흐름)**:
       - **Hook (도입)**: 독자의 고민을 바로 찌르세요. ("아이가 연습하기 싫어하나요?", "퇴근하고 뭐 할지 고민되시죠?") 그리고 "이 글에서 해결해 드립니다"라고 선언하세요.
       - **Body (본문)**: 줄글보다는 **소제목 + 리스트(1, 2, 3)** 형태로 가독성을 극대화하세요. 핵심 내용은 **볼드체**로 강조하세요.
       - **Tip (정보)**: 선생님의 메모 내용을 바탕으로 실질적인 '꿀팁'이나 '솔루션'을 제시하세요.
       - **Conclusion (결말)**: "더 궁금하면 톡톡 주세요", "체험 레슨 이벤트 중" 등 명확한 행동(CTA)을 유도하세요.

    3. **톤앤매너**:
       - 빠르고 경쾌한 리듬감. (지루하면 이탈합니다!)
       - 적절한 이모지 사용 (✅, 💡, 🔥, 👉)으로 시선을 잡으세요.
       - 어려운 음악 용어는 쉽게 풀어서 설명하세요.

    4. **형식**:
       - 중간중간 `[사진: ~~ (예: 비포/애프터 비교샷)]` 가이드를 넣어 시각적 흥미를 유도하세요.

    [목표]
    검색해서 들어온 사람이 "오, 꿀팁 얻었다!" 하고 공감 누르고 가게 만드는 것.
    """

    if not api_key:
        return "⚠️ API 키를 먼저 설정해주세요!"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        
        print(f"🔥 대중 픽(Viral Ver.) 글 쓰는 중... (주제: {topic})")
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ 에러가 발생했습니다: {e}"

# ==========================================
# 3. 실행 (Run)
# ==========================================
if __name__ == "__main__":
    print(f"--- {STUDIO_NAME} 블로그 포스팅 도우미 (Viral/Info Ver.) ---")
    
    # 입력 예시 가이드
    print("팁: '꿀팁', '해결법', '비교' 같은 주제가 잘 먹힙니다.")
    print("예: '바이올린 가격대별 차이점', '성인 취미 3개월 현실 후기', '학원 고를 때 호갱 안 되는 법'\n")

    topic_in = input("주제 입력 (예: 바이올린 10만 원대 vs 100만 원대 차이): ")
    notes_in = input("메모 입력 (카톡 내용 등): ")

    if not topic_in: topic_in = "다산신도시 엄마들이 바이올린 학원 고를 때 가장 많이 하는 실수 BEST 3"
    if not notes_in: notes_in = "1. 거리만 보고 고름(케어가 중요). 2. 무조건 싼 악기 삼(소리 안 나서 흥미 잃음). 3. 진도 빨리 나가는 것만 좋아함(기초 무너짐). 우리 학원은 이 3가지를 다 해결해줌."

    post = generate_viral_blog_post(topic_in, notes_in)

    # 파일 저장
    filename = f"blog_viral_{datetime.now().strftime('%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(post)

    print(f"\n✅ 대중 노출형 원고 작성 완료! '{filename}' 파일을 확인해 주세요.")
    print("제목이 낚시성(?) 같아도 클릭률은 확실할 겁니다!")