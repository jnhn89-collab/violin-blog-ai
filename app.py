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

# ==============================================================================
# 0. 시스템 설정 & Streamlit UI 초기화
# ==============================================================================
st.set_page_config(page_title="Violin Blog Master", page_icon="🎻", layout="wide")

# API 키 로드 (Secrets 우선)
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
api_key = os.environ.get("GOOGLE_API_KEY")

# 모듈 매핑
MODULE_NAMES = {
    "VIRAL": "naver_blog_mass_appeal",
    "ELEGANT": "naver_blog_elegant",
    "KIDS": "naver_blog_kids_lesson_promo",
    "SEASON": "naver_blog_SEASON_special"
}

# 세션 상태 초기화
if "result_zip" not in st.session_state:
    st.session_state.result_zip = None
if "preview_html" not in st.session_state:
    st.session_state.preview_html = None

# ==============================================================================
# 1. Agent Classes (선생님의 원본 로직 100% 보존)
# ==============================================================================

class DirectorAgent:
    """총괄 기획: 사용자의 의도를 파악하고 모드를 결정"""
    def get_mode_from_ui(self):
        # 웹 UI에서는 input() 대신 사이드바 선택
        with st.sidebar:
            st.header("🎬 Director Agent")
            mode = st.radio(
                "작전 모드 선택",
                ("VIRAL (정보성/다산정보통)", "ELEGANT (감성/우아한원장)", "KIDS (유아/친절한쌤)", "SEASON (방학/전략가)"),
                index=0
            )
            st.info(f"현재 모드: {mode.split()[0]}")
            return mode.split()[0]

class WriterAgent:
    """글쓰기: 외부 모듈(.py)을 동적으로 로드하여 초안 작성"""
    def write_draft(self, mode, topic, notes):
        module_name = MODULE_NAMES[mode]
        # st.toast(f"📝 Writer: '{module_name}.py' 전문가 호출 중...", icon="🏃")
        
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module) # 모듈 수정 시 즉시 반영을 위해 리로드
            
            if mode == "VIRAL": return module.generate_viral_blog_post(topic, notes)
            elif mode == "ELEGANT": return module.generate_real_blog_post(topic, notes)
            elif mode == "KIDS": return module.agent_blog_writer(topic, notes)
            elif mode == "SEASON": return module.generate_SEASON_special_post(topic, notes)
                
        except ImportError:
            return f"❌ 오류: '{module_name}.py' 파일이 없습니다."
        except Exception as e:
            return f"❌ 오류 발생: {e}"

class EditorAgent:
    """편집: 초안을 HTML로 변환하고 이미지 위치 기획"""
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def edit_to_html(self, raw_text, mode):
        style_guide = {
            "VIRAL": "핵심 키워드 볼드 처리, 리스트 활용, 명쾌한 어조",
            "ELEGANT": "우아한 인용구 활용, 여백의 미, 감성적인 문단 나눔",
            "KIDS": "따뜻한 대화체 유지, 중요한 육아 정보 강조",
            "SEASON": "긴박감 넘치는 강조 처리, 커리큘럼 표 스타일링"
        }

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
    """프롬프트 엔지니어: 한국어 상황 묘사를 고품질의 영어 AI 그림 프롬프트로 번역합니다"""
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')

    def create_prompt(self, korean_desc, mode):
        themes = {
            "VIRAL": "Clean, bright professional photography, minimalist",
            "ELEGANT": "Cinematic lighting, warm atmosphere, shallow depth of field",
            "KIDS": "Soft pastel tones, cute and heartwarming, bright studio",
            "SEASON": "Cozy SEASON atmosphere, focused study environment"
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
    """화가: Imagen 3 API 호출 및 이미지 생성 (메모리상에 저장)"""
    def __init__(self, api_key):
        self.api_key = api_key
        # REST API URL
        self.model_name = "imagen-4.0-ultra-generate-preview-06-06" 
        self.api_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:predict"

    def draw_to_bytes(self, prompt):
        headers = {"Content-Type": "application/json"}
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1, "aspectRatio": "4:3"}
        }
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(self.url, data=data, headers=headers)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                if "predictions" in result:
                    b64 = result["predictions"][0]["bytesBase64Encoded"]
                    return base64.b64decode(b64)
        except Exception as e:
            return None # 실패 시 None 반환

# ==============================================================================
# 2. Main UI & Orchestration
# ==============================================================================

st.title("🎻 Violin Blog Master")
st.markdown("**Agent-Based** Professional Blog Post Generator")

if not api_key:
    st.error("🚨 API Key가 없습니다. Secrets에 설정해주세요.")
    st.stop()

# 1. 기획 (Director)
director = DirectorAgent()
current_mode = director.get_mode_from_ui()

col1, col2 = st.columns([3, 1])
with col1:
    topic = st.text_input("주제", placeholder="예: 7세 바이올린 첫 수업")
with col2:
    # 주제 추천 기능 (간단하게 구현)
    if st.button("🎲 주제 추천"):
         genai.configure(api_key=api_key)
         rec_model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
         rec = rec_model.generate_content(f"Random하게 리서치하여 바이올린 개인레슨 블로그 주제 10개 추천 후 5개 랭킹매겨서 첫번째꺼 제공. 모드: {current_mode}. 제목만 나열.")
         st.toast(rec.text)

notes = st.text_area("메모 / 핵심 내용", height=100)

# 실행 버튼
if st.button("🚀 에이전트 팀 호출 (Start)", type="primary"):
    if not topic:
        st.warning("주제를 입력해주세요.")
    else:
        # 상태창 생성
        status = st.status("🚀 [Violin Blog Master] 시스템 가동 중...", expanded=True)
        
        try:
            # 2. 글쓰기 (Writer)
            writer = WriterAgent()
            status.write(f"📝 [Writer] '{current_mode}' 전문 작가가 글을 쓰는 중입니다...")
            draft = writer.write_draft(current_mode, topic, notes)
            
            if "❌" in draft:
                status.update(label="오류 발생", state="error")
                st.error(draft)
                st.stop()

            # 3. 편집 (Editor)
            editor = EditorAgent(api_key)
            status.write("✨ [Editor] 네이버 블로그 포맷으로 편집 중입니다...")
            html_content = editor.edit_to_html(draft, current_mode)

            # 4. 미술 (Art Director & Painter)
            art_director = ArtDirectorAgent(api_key)
            painter = PainterAgent(api_key)
            
            image_requests = re.findall(r"\[IMAGE_REQ: (.*?)\]", html_content)
            generated_images = [] # (파일명, 바이너리)
            
            final_html = html_content
            
            if image_requests:
                prog_bar = status.progress(0)
                status.write(f"🎨 [Painter] 총 {len(image_requests)}장의 이미지를 그리기 시작합니다.")
                
                for idx, req in enumerate(image_requests):
                    # 프롬프트 생성
                    eng_prompt = art_director.create_prompt(req, current_mode)
                    status.write(f"  └─ 🖌️ 그리는 중 ({idx+1}/{len(image_requests)}): {req}")
                    
                    # 그림 생성
                    img_bytes = painter.draw_to_bytes(eng_prompt)
                    
                    if img_bytes:
                        fname = f"image_{idx+1}.png"
                        generated_images.append((fname, img_bytes))
                        
                        # HTML 태그 교체 (블로그 붙여넣기 가이드용)
                        replace_html = f"""
                        <div align="center" style="margin: 20px 0; border: 2px dashed #ccc; padding: 20px;">
                            <span style="color: #888; font-weight: bold;">[이곳에 '{fname}' 이미지를 넣으세요]</span><br>
                            <img src="{fname}" style="max-width: 300px; opacity: 0.5; margin-top: 10px;">
                        </div>
                        """
                        final_html = final_html.replace(f"[IMAGE_REQ: {req}]", replace_html, 1)
                    
                    prog_bar.progress((idx + 1) / len(image_requests))

            # 결과 저장
            st.session_state.preview_html = final_html
            
            # ZIP 파일 생성 (메모리 상에서)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                # HTML 추가
                full_html_doc = f"<html><body>{final_html}</body></html>"
                zf.writestr("index.html", full_html_doc)
                # 이미지 추가
                for fname, data in generated_images:
                    zf.writestr(fname, data)
            
            st.session_state.result_zip = zip_buffer.getvalue()
            
            status.update(label="✅ 모든 에이전트 작업 완료!", state="complete", expanded=False)

        except Exception as e:
            status.update(label="시스템 오류", state="error")
            st.error(f"Error: {e}")

# ==============================================================================
# 3. Result View (결과 확인 및 다운로드)
# ==============================================================================
if st.session_state.result_zip:
    st.divider()
    
    st.subheader("📦 작업 결과물")
    
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.info("아래 코드를 복사해서 네이버 블로그 [HTML 모드]가 아니라 그냥 붙여넣으세요.")
        st.code(st.session_state.preview_html, language="html")
        
    with col_b:
        st.success("이미지와 원고가 준비되었습니다.")
        st.download_button(
            label="📥 전체 패키지 다운로드 (.zip)",
            data=st.session_state.result_zip,
            file_name="blog_package.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )
        st.caption("압축을 풀고 이미지를 블로그 해당 위치에 드래그하세요.")

