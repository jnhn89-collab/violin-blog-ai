import streamlit as st
import os
import re
import time
import zipfile
import io
import importlib
import google.generativeai as genai
import json
import base64
import urllib.request
import urllib.error

# ==========================================
# 1. 설정 및 UI 구성
# ==========================================
st.set_page_config(page_title="Violin Blog Master", page_icon="🎻", layout="wide")

st.title("🎻 Violin Blog Master Web")
st.markdown("### AI 에이전트 팀이 작성하는 고품질 블로그 포스팅")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    
    # API 키 입력 (보안을 위해 비밀번호 형식)
    api_key_input = st.text_input("Google API Key", type="password", placeholder="AIzaSy...")
    if api_key_input:
        os.environ["GOOGLE_API_KEY"] = api_key_input
        genai.configure(api_key=api_key_input)
    
    st.divider()
    
    # 모드 선택
    mode = st.radio(
        "모드 선택",
        ("VIRAL (정보성/노출)", "ELEGANT (감성/철학)", "KIDS (유아/초등)", "WINTER (방학특강)"),
        index=0
    )
    mode_key = mode.split()[0]  # "VIRAL" 등 키워드만 추출

# ==========================================
# 2. 에이전트 클래스 (웹 환경에 맞게 수정)
# ==========================================

MODULE_NAMES = {
    "VIRAL": "naver_blog_mass_appeal",
    "ELEGANT": "naver_blog_elegant",
    "KIDS": "naver_blog_kids_lesson_promo",
    "WINTER": "naver_blog_winter_special"
}

def get_writer_draft(mode, topic, notes):
    module_name = MODULE_NAMES[mode]
    try:
        module = importlib.import_module(module_name)
        if mode == "VIRAL": return module.generate_viral_blog_post(topic, notes)
        elif mode == "ELEGANT": return module.generate_real_blog_post(topic, notes)
        elif mode == "KIDS": return module.agent_blog_writer(topic, notes)
        elif mode == "WINTER": return module.generate_winter_special_post(topic, notes)
    except Exception as e:
        return f"❌ 오류 발생: {e}"

def edit_to_html(api_key, raw_text, mode):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    style_guide = {
        "VIRAL": "핵심 키워드 볼드 처리, 리스트 활용, 명쾌한 어조",
        "ELEGANT": "우아한 인용구 활용, 여백의 미, 감성적인 문단 나눔",
        "KIDS": "따뜻한 대화체 유지, 중요한 육아 정보 강조",
        "WINTER": "긴박감 넘치는 강조 처리, 커리큘럼 표 스타일링"
    }

    prompt = f"""
    당신은 네이버 블로그 편집장입니다. 아래 [초안]을 HTML 원고로 재작성하세요.
    
    [초안]: {raw_text}
    
    [지시사항]
    1. 줄바꿈은 `<br>`, 소제목은 `<h3>` (노란색 밑줄 스타일) 사용.
    2. 강조는 `<b><span style='background-color: #fff5b1;'>` 사용.
    3. 이미지가 들어갈 위치에 `[IMAGE_REQ: (구체적 묘사)]` 태그 삽입.
    4. 스타일: {style_guide.get(mode)}
    5. 오직 HTML 코드만 출력 (마크다운 없이).
    """
    response = model.generate_content(prompt)
    return response.text.strip().replace("```html", "").replace("```", "")

def create_image_prompt(api_key, korean_desc, mode):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash') # 속도를 위해 Flash 사용 권장
    
    themes = {
        "VIRAL": "Clean, bright professional photography, minimalist",
        "ELEGANT": "Warm cinematic lighting, emotional atmosphere, shallow depth of field",
        "KIDS": "Soft pastel tones, cute and heartwarming",
        "WINTER": "Cozy winter atmosphere, focused study environment"
    }
    
    prompt = f"""
    Transform this Korean description into a high-quality English prompt for 'Imagen 3'.
    Theme: {themes.get(mode)}
    Input: {korean_desc}
    Output ONLY the English prompt.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def generate_image_bytes(api_key, prompt):
    # Imagen API 호출 (REST 방식)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "4:3"}
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            if "predictions" in result:
                b64 = result["predictions"][0]["bytesBase64Encoded"]
                return base64.b64decode(b64)
    except Exception as e:
        st.error(f"이미지 생성 실패: {e}")
        return None

# ==========================================
# 3. 메인 로직
# ==========================================

# 입력 폼
col1, col2 = st.columns([3, 1])
with col1:
    topic = st.text_input("글 주제", placeholder="예: 7세 아이 바이올린 첫 수업 후기")
with col2:
    if st.button("추천 주제 받기"):
        st.info("기능 준비 중입니다! (Kids 모드 참조)")

notes = st.text_area("메모/강조점", placeholder="카톡 내용이나 강조하고 싶은 내용을 적어주세요.", height=100)

if st.button("🚀 블로그 포스팅 생성 시작", type="primary"):
    if not api_key_input:
        st.error("⚠️ API 키를 먼저 입력해주세요!")
    elif not topic:
        st.warning("주제를 입력해주세요.")
    else:
        # 1. 글쓰기 단계
        with st.status("📝 글을 쓰고 있습니다...", expanded=True) as status:
            st.write("Writer Agent가 초안을 작성 중입니다...")
            draft = get_writer_draft(mode_key, topic, notes)
            
            st.write("Editor Agent가 HTML로 변환 중입니다...")
            html_content = edit_to_html(api_key_input, draft, mode_key)
            status.update(label="글 작성 완료! 이미지를 생성합니다.", state="running")
            
            # 2. 이미지 생성 단계
            image_requests = re.findall(r"\[IMAGE_REQ: (.*?)\]", html_content)
            generated_images = [] # (파일명, 바이너리데이터) 튜플 리스트
            
            final_html = html_content
            
            if image_requests:
                progress_bar = st.progress(0)
                for idx, req in enumerate(image_requests):
                    st.write(f"🎨 그림 그리는 중 ({idx+1}/{len(image_requests)}): {req}")
                    
                    eng_prompt = create_image_prompt(api_key_input, req, mode_key)
                    img_data = generate_image_bytes(api_key_input, eng_prompt)
                    
                    if img_data:
                        fname = f"image_{idx+1}.png"
                        generated_images.append((fname, img_data))
                        
                        # HTML 내 태그 교체
                        replacement = f"""<br><div align='center'><img src='{fname}' style='max-width:100%; border-radius:10px;'><br><span style='color:#888; font-size:12px;'>{fname}</span></div><br>"""
                        final_html = final_html.replace(f"[IMAGE_REQ: {req}]", replacement, 1)
                    
                    progress_bar.progress((idx + 1) / len(image_requests))
            
            status.update(label="✅ 모든 작업이 완료되었습니다!", state="complete")

        # 3. 결과 보여주기 및 다운로드
        st.divider()
        st.subheader("🎉 완성된 결과물")
        
        # 미리보기 탭
        tab1, tab2 = st.tabs(["📱 미리보기", "💻 HTML 코드"])
        
        with tab1:
            st.markdown(final_html, unsafe_allow_html=True)
            # 스트림릿에서 로컬 이미지 경로를 바로 못 읽으므로, 
            # 미리보기에서는 이미지가 깨져 보일 수 있음을 안내하거나 
            # base64로 변환해서 보여주는 로직이 추가로 필요할 수 있음. 
            # 여기서는 다운로드를 유도하는 것이 깔끔함.
            st.warning("ℹ️ 위 미리보기에서 이미지가 엑박으로 보이는 것은 정상입니다. 다운로드 후 폴더를 확인하세요!")
            
            # 생성된 이미지들 갤러리로 보여주기
            if generated_images:
                st.write("### 생성된 이미지 확인")
                cols = st.columns(len(generated_images))
                for i, (fname, data) in enumerate(generated_images):
                    with cols[i]:
                        st.image(data, caption=fname)

        with tab2:
            st.code(final_html, language="html")

        # 4. ZIP 다운로드 버튼 생성
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            # HTML 파일 추가
            full_html = f"<html><body>{final_html}</body></html>"
            zf.writestr("index.html", full_html)
            
            # 이미지 파일들 추가
            for fname, data in generated_images:
                zf.writestr(fname, data)
        
        st.download_button(
            label="📦 전체 파일 다운로드 (HTML + 이미지)",
            data=zip_buffer.getvalue(),
            file_name="blog_post_package.zip",
            mime="application/zip",
            type="primary"
        )