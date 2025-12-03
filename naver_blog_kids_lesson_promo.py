import os
import google.generativeai as genai
from datetime import datetime

# ==========================================
# 1. 설정 (Setup)
# ==========================================


api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("⚠️ 경고: API 키가 설정되지 않았습니다.")

STUDIO_NAME = "다산 라미 바이올린"
LOCATION = "남양주 다산신도시"

# ==========================================
# 2. Agent 1: 주제 선정 요원 (Strategist)
# ==========================================
def agent_topic_selector(target_age):
    """
    타겟 연령대(유아/초등)에 맞춰, 학부모가 반응할 만한 마케팅 소구점(Hook)을 찾아 주제를 제안합니다.
    """
    print(f"\n🕵️ [Agent 1] {target_age} 대상 인기 키워드 분석 중...")
    
    prompt = f"""
    당신은 {LOCATION}의 아동 음악 교육 마케팅 전략가입니다.
    타겟 대상인 **'{target_age} 학부모'**들이 현재 가장 고민하고 관심을 가질만한 블로그 주제 5가지를 선정하세요.
    
    [분석 관점]
    1. **두뇌/신체 발달**: 소근육 발달, 좌뇌우뇌 균형, 바른 자세.
    2. **정서/성격**: 산만한 아이 집중력, 수줍은 아이 자신감, 정서적 안정.
    3. **흥미/놀이**: "바이올린은 어렵다"는 편견 깨기, 놀이로 배우는 음악.
    4. **학교 생활**: 초등 입학 준비, 수행평가, 오케스트라 활동.
    
    [출력 형식]
    1. [집중력] 산만한 우리 아이, 엉덩이 힘 기르는 법
    2. [두뇌발달] ...
    (이런 식으로 번호와 카테고리, 매력적인 제목을 5개 나열하세요.)
    """
    
    if not api_key:
        return "API 키가 필요합니다."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Agent 1 오류: {e}"

# ==========================================
# 3. Agent 2: 글쓰기 요원 (Writer)
# ==========================================
def agent_blog_writer(selected_topic, raw_notes):
    """
    선정된 주제를 바탕으로 아동 교육 전문가의 시선에서 따뜻하고 설득력 있는 글을 씁니다.
    """
    print(f"\n✍️ [Agent 2] '{selected_topic}' 주제로 원고 작성 중...")
    
    prompt = f"""
    당신은 {LOCATION}에서 아이들을 진심으로 사랑하는 **'유아/초등 전문 바이올린 개인레슨 선생님'**입니다.
    Agent 1이 선정한 주제 **"{selected_topic}"**에 대해 블로그 글을 작성하세요.
    
    [입력 메모]: "{raw_notes}"

    [톤앤매너: Warm & Professional]
    - "어머니, 우리 아이가..." 와 같이 학부모에게 조곤조곤 상담하듯 대화체를 사용하세요.
    - 아이를 '가르치는 대상'이 아니라 '잠재력을 가진 씨앗'으로 바라보는 시선을 담으세요.
    - 전문 용어(소근육, 청각 발달 등)를 쓰되, 아주 쉽게 풀어서 설명하세요.

    [글의 구조]
    1. **공감(Empathy)**: 육아의 고민(산만함, 스마트폰 중독, 소심함 등)을 위로하며 시작.
    2. **솔루션(Violin)**: 바이올린이 단순한 악기가 아니라, 그 고민의 해결책(놀이, 치유, 발달도구)임을 제시.
    3. **증거(Story)**: 선생님의 메모 내용을 바탕으로 실제 아이의 변화 사례 묘사.
    4. **약속(Promise)**: "음악을 사랑하는 아이로 키우겠습니다"라는 교육 철학 제시.
    5. **안내(Guide)**: 체험 레슨 안내 (유아 전용 악기 완비, 1:1 눈높이 수업 등).

    [형식]
    - 중간중간 `[사진: 아이가 고사리 같은 손으로 활을 잡은 모습]` 처럼 구체적인 사진 가이드를 넣으세요.
    - 가독성을 위해 문단을 자주 나누세요.
    """
    
    try:
        model = genai.GenerativeModel('gemini-3-pro-preview')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Agent 2 오류: {e}"

# ==========================================
# 4. 메인 실행 (Cooperation)
# ==========================================
if __name__ == "__main__":
    print(f"--- 🎻 {STUDIO_NAME} 유아/초등 홍보 시스템 가동 ---")
    
    # 1단계: 타겟 설정 및 주제 추천
    target = input("타겟 연령을 입력하세요 (예: 6-7세 유아, 초등 1-2학년): ")
    if not target: target = "7세 예비 초등학생"
    
    topics = agent_topic_selector(target)
    print("\n" + "="*20 + " [추천 주제 리스트] " + "="*20)
    print(topics)
    print("="*60)
    
    # 2단계: 주제 선택 및 메모 입력
    choice = input("\n맘에 드는 주제를 복사해서 붙여넣거나, 직접 입력하세요: ")
    if not choice: choice = "바이올린으로 기르는 우리 아이 집중력"
    
    notes = input("관련된 에피소드나 강조하고 싶은 점 (메모): ")
    if not notes: notes = "처음엔 5분도 못 앉아있던 아이가, 좋아하는 동요를 연주하고 싶어서 20분 동안 집중해서 연습함. 작은 성공 경험이 중요함."
    
    # 3단계: 글 작성
    post = agent_blog_writer(choice, notes)
    
    # 저장
    filename = f"blog_kids_{datetime.now().strftime('%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(post)
        
    print(f"\n✅ 원고 작성 완료! '{filename}' 파일을 확인하세요.")