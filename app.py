import streamlit as st
import os
import re
import time
import importlib
import google.generativeai as genai
from datetime import datetime
import json
import base64
import urllib.request
import urllib.error
import zipfile
import io
import random

# ==============================================================================
# 0. 시스템 설정 & Streamlit UI 초기화
# ==============================================================================
st.set_page_config(page_title="Violin Blog Master", page_icon="🎻", layout="wide")

# [CSS 수정] 모바일 최적화 + 블로그 미리보기 스타일(Paper Style)
st.markdown("""
    <style>
        /* 모바일 상단 여백 및 헤더 숨김 */
        .block-container { padding-top: 1.5rem !important; padding-bottom: 3rem !important; }
        header { visibility: hidden; }
        header:hover { visibility: visible; }
        
        /* [핵심] 블로그 미리보기 종이 스타일 */
        .blog-preview-box {
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            color: black;
            font-family: 'Nanum Gothic', sans-serif;
            line-height: 1.8;
            margin-bottom: 20px;
        }
        /* 네이버 블로그 느낌의 소제목 스타일 */
        .blog-preview-box h3 {
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        /* 드래그 선택 시 색상 */
        ::selection {
            background: #ffeb3b;
            color: black;
        }
    </style>
""", unsafe_allow_html=True)

# API 키 로드
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
api_key = os.environ.get("GOOGLE_API_KEY")

MODULE_NAMES = {
    "VIRAL": "naver_blog_mass_appeal",
    "ELEGANT": "naver_blog_elegant",
    "KIDS": "naver_blog_kids_lesson_promo",
    "SEASON": "naver_blog_SEASON_special"
}

if "input_topic" not in st.session_state: st.session_state.input_topic = ""
if "input_notes" not in st.session_state: st.session_state.input_notes = ""
if "result_zip" not in st.session_state: st.session_state.result_zip = None
if "preview_html" not in st.session_state: st.session_state.preview_html = None

# ==============================================================================
# 1. Agent Classes (로직 동일)
# ==============================================================================

class DirectorAgent:
    def get_mode_from_ui(self):
        with st.sidebar:
            st.header("🎬 Director Agent")
            mode = st.radio("작전 모드", ("VIRAL (정보성)", "ELEGANT (감성)", "KIDS (유아)", "SEASON (특강)"), index=0)
            return mode.split()[0]

    def generate_random_content(self, api_key):
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = """
        당신은 창의적인 바이올린 학원 마케팅 디렉터입니다.
        아래 5가지 컨셉 중 하나를 랜덤하게 골라, 창의적이고 트렌디한 블로그 글 주제와 선생님의 메모를 작성하세요.
        
        [컨셉 후보]
        1. 정보성 (바이올린 가격, 관리법, 학원 고르는 팁)
        2. 감성/철학 (음악이 주는 힘, 아이의 성장, 계절감)
        3. 유아/초등 (소근육 발달, 집중력, 아이 눈높이 교육)
        4. 음악 전공/전문가 (입시, 콩쿠르, 디테일한 테크닉, 전공생 멘탈관리)
        5. 방학 특강 (단기 완성, 방학 알차게 보내기, 새학기 대비)

        [요청사항]
        - 주제: 사람들의 클릭을 유도하는 매력적인 제목 스타일 또는 바이올린 개인레슨과 관련된 주제
        - 메모: 선생님이 겪은 구체적인 에피소드나 강조하고 싶은 핵심 포인트 (150자 내외)
        - 출력: 오직 JSON 형식으로만 주세요. {"topic": "...", "notes": "..."}
        """
        try:
            response = model.generate_content(prompt)
            text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(text)
        except:
            return {"topic": "주제 생성 실패", "notes": "다시 시도해주세요."}

class WriterAgent:
    def write_draft(self, mode, topic, notes):
        module_name = MODULE_NAMES[mode]
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)
            if mode == "VIRAL": return module.generate_viral_blog_post(topic, notes)
            elif mode == "ELEGANT": return module.generate_real_blog_post(topic, notes)
            elif mode == "KIDS": return module.agent_blog_writer(topic, notes)
            elif mode == "SEASON": return module.generate_SEASON_special_post(topic, notes)
        except Exception as e: return f"❌ 오류: {e}"

class EditorAgent:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def edit_to_html(self, raw_text, mode):

        style_guide = {
            "VIRAL": "핵심 키워드 볼드 처리, 리스트 활용, 명쾌한 어조",
            "ELEGANT": "우아한 인용구 활용, 여백의 미, 감성적인 문단 나눔",
            "KIDS": "따뜻한 대화체 유지, 중요한 육아 정보 강조",
            "WINTER": "긴박감 넘치는 강조 처리, 커리큘럼 표 스타일링"
        }
        # [핵심 수정] 네이버 스마트 에디터와 호환성 높은 스타일 적용
        prompt = f"""
        당신은 네이버 블로그 편집장입니다. 아래 [초안]을 바탕으로 블로그에 바로 붙여넣을 수 있는 **완벽한 HTML 원고**로 재작성하세요.
        
        [초안]:
        {raw_text}
        
        [작업 지시사항]
        1. **HTML 포맷팅**:
           - 줄바꿈은 `<br>` 태그를 사용하세요. (문단 사이는 `<br><br>`)
           - 소제목은 `<h3 style="color: #000; border-left: 5px solid #ffcc00; padding-left: 10px; margin: 30px 0 15px;">` 스타일을 적용하세요.
           - 강조하고 싶은 문장은 `<b><span style="background-color: #fff5b1;">` (형광펜 효과) 등으로 꾸미세요.
           - 인용구는 `<blockquote style="border: 1px solid #ddd; padding: 20px; background: #f9f9f9;">`를 사용하세요.
        
        2. **이미지 기획 (중요)**:
           - 글의 흐름상 이미지가 들어가면 좋은 위치(최소 3곳 이상)에 `[IMAGE_REQ: (이미지에 대한 아주 구체적이고 글의 흐름에 맞는 묘사 500자 이상)]` 태그를 삽입하세요.
           - **주의**: `<img>` 태그를 쓰지 말고, `[IMAGE_REQ: ...]` 텍스트 그대로 남기세요. 이것은 다음 단계의 화가(Painter)에게 보낼 지령입니다.
        
        3. **스타일 가이드**: {style_guide.get(mode, "가독성 좋게")}
        
        오직 결과물 HTML 코드만 출력하세요. (마크다운 코드블록 없이)
        """
        response = self.model.generate_content(prompt)
        return response.text.strip().replace("```html", "").replace("```", "")

class ArtDirectorAgent:
    """프롬프트 엔지니어: 한국어 상황 묘사를 고품질의 영어 AI 그림 프롬프트로 번역합니다."""
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')

    def create_prompt(self, korean_desc, mode):
        # 블로그 전체 테마 유지 (일관성)
        themes = {
            "VIRAL": "Clean, bright professional photography style, high contrast, minimalist infographic vibe",
            "ELEGANT": "Warm cinematic lighting, emotional atmosphere, shallow depth of field, classical music aesthetic, high resolution",
            "KIDS": "Soft pastel tones, cute and heartwarming, educational illustration style or bright photography",
            "WINTER": "Cozy winter atmosphere, focused study environment, warm indoor lighting, snow outside window hint"
        }
        theme_prompt = themes.get(mode, "High quality photography")
        
        prompt = f"""
        Act as a world-class AI Art Director and Visual Creative Lead specializing in cinematic storytelling, fine-art composition, and editorial-grade concept development.

        Your task: Transform the following Korean description into a meticulously detailed, professional-quality English prompt optimized for ‘Imagen 3.0’. Go beyond simple translation—elevate the concept with artistic depth, emotional tone, atmosphere, lighting, composition, and stylistic direction.

        Requirements for the output prompt:
        - SUPER HYPER REALISM SO EVEN CANNOT DISTINGUISH
        - Ultra-clear subject framing, artistic perspective, and visual intention
        - Specific camera language (e.g., focal length, angle, depth-of-field)
        - Detailed lighting style (e.g., soft diffused morning light, dramatic rim lighting)
        - Mood, texture, color palette, and artistic influences
        - Environmental and contextual storytelling elements
        - Physical details: gesture, expressions, posture, movement
        - Editorial or fine-art tone suitable for premium visual generation
        - Avoid generic phrases; prioritize evocative, purposeful description

        Use this structure during enhancement:
        1. Overall artistic concept
        2. Subject details & emotional expression
        3. Environment, composition & camera direction
        4. Lighting style & color palette
        5. Texture, mood & artistic influences

        [Input Description]: {korean_desc}
        [Overall Theme]: {theme_prompt}
        [Subject]: Violin, Music Education, Students, Teacher.

        Output ONLY the final, polished English prompt string—no explanations.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

class PainterAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model_name = "imagen-4.0-ultra-generate-preview-06-06" 
        self.api_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:predict"

    def draw_to_bytes(self, prompt):
        headers = {"Content-Type": "application/json"}
        payload = {"instances": [{"prompt": prompt}], "parameters": {"sampleCount": 1, "aspectRatio": "4:3"}}
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(self.url, data=data, headers=headers)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                if "predictions" in result:
                    return base64.b64decode(result["predictions"][0]["bytesBase64Encoded"])
        except: return None

# ==============================================================================
# 2. Main UI & Orchestration
# ==============================================================================
st.title("🎻 Violin Blog Master")
if not api_key: st.error("🚨 API Key가 없습니다."); st.stop()

director = DirectorAgent()
current_mode = director.get_mode_from_ui()

def apply_magic_fill():
    with st.spinner("🎲 AI가 생각 중..."):
        c = director.generate_random_content(api_key)
        st.session_state.input_topic = c['topic']
        st.session_state.input_notes = c['notes']

col1, col2 = st.columns([0.7, 0.3], gap="small")
with col1: st.write(""); st.subheader("📝 주제 및 메모")
with col2: st.button("🎲 랜덤 자동채움", on_click=apply_magic_fill, use_container_width=True)

topic = st.text_input("주제", value=st.session_state.input_topic, placeholder="작성할 글의 주제", key="topic_input")
notes = st.text_area("메모", value=st.session_state.input_notes, height=150, placeholder="핵심 내용", key="notes_input")

if st.button("🚀 에이전트 팀 호출 (Start)", type="primary", use_container_width=True):
    if not topic: st.warning("주제를 입력하세요.")
    else:
        status = st.status("🚀 작업 시작...", expanded=True)
        try:
            # 1. Writer
            writer = WriterAgent()
            status.write(f"📝 글 쓰는 중 ({current_mode})...")
            draft = writer.write_draft(current_mode, topic, notes)
            
            # 2. Editor
            editor = EditorAgent(api_key)
            status.write("✨ 예쁘게 꾸미는 중...")
            html_content = editor.edit_to_html(draft, current_mode)

            # 3. Art & Painter
            art = ArtDirectorAgent(api_key)
            paint = PainterAgent(api_key)
            reqs = re.findall(r"\[IMAGE_REQ: (.*?)\]", html_content)
            imgs = []
            final_html = html_content
            
            if reqs:
                pbar = status.progress(0)
                status.write(f"🎨 이미지 {len(reqs)}장 생성 중...")
                for i, r in enumerate(reqs):
                    pbar.progress((i)/len(reqs))
                    p = art.create_prompt(r, current_mode)
                    b = paint.draw_to_bytes(p)
                    if b:
                        fname = f"image_{i+1}.png"
                        imgs.append((fname, b))
                        # [핵심] 복사 붙여넣기 시 이미지 자리를 시각적으로 보여줌
                        rep = f"""<br><div style='background:#f1f3f5; padding:20px; text-align:center; border-radius:10px; margin: 10px 0;'>📸 <b>이미지 자리 ({fname})</b><br><span style='font-size:0.8em; color:#888;'>이곳에 다운받은 이미지를 넣으세요</span></div><br>"""
                        final_html = final_html.replace(f"[IMAGE_REQ: {r}]", rep, 1)
                pbar.progress(1.0)

            st.session_state.preview_html = final_html
            
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as zf:
                zf.writestr("index.html", f"<html><body>{final_html}</body></html>")
                for f, d in imgs: zf.writestr(f, d)
            st.session_state.result_zip = zip_buf.getvalue()
            
            status.update(label="✅ 완성되었습니다!", state="complete", expanded=False)
        except Exception as e: status.update(label="에러 발생", state="error"); st.error(e)

# ==============================================================================
# 3. 결과 뷰 (여기가 핵심 변경됨)
# ==============================================================================
if st.session_state.result_zip:
    st.divider()
    st.subheader("🎉 완성된 원고")
    
    # 상단 안내
    st.info("💡 **사용법**: 아래 하얀 박스 안의 내용을 **마우스로 드래그해서 복사(Ctrl+C)** 한 뒤, 네이버 블로그에 **붙여넣기(Ctrl+V)** 하세요. (이미지는 따로 넣어주세요)")

    # 1. 렌더링된 미리보기 (복사용)
    # st.code 대신 st.markdown(unsafe_allow_html=True)를 사용하여 실제 적용된 스타일을 보여줌
    st.markdown(f"""
        <div class="blog-preview-box">
            {st.session_state.preview_html}
        </div>
    """, unsafe_allow_html=True)

    # 2. 이미지 다운로드
    if st.session_state.result_zip:
        st.download_button(
            label="📦 이미지 전체 다운로드 (ZIP)",
            data=st.session_state.result_zip,
            file_name="blog_images.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )

