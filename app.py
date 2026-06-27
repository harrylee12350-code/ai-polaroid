import streamlit as st
from PIL import Image, ImageDraw
import imageio
import io
import time
from datetime import datetime

# --- 1. 페이지 기본 설정 ---
st.set_page_config(page_title="AI 폴라로이드 스튜디오", page_icon="📸", layout="centered")

# --- 2. 세션 상태(임시 데이터) 초기화 ---
if 'remaining_films' not in st.session_state:
    st.session_state.remaining_films = 5
if 'step' not in st.session_state:
    st.session_state.step = "select_theme"
if 'gif_bytes' not in st.session_state:
    st.session_state.gif_bytes = None

# --- 3. 상단 고정 헤더 ---
st.markdown("<h1 style='text-align: center; color: #1a303a;'>📸 AI 폴라로이드</h1>", unsafe_allow_html=True)
st.markdown(
    f"<h4 style='text-align: center; color: #b34a3b;'>🎞️ 오늘 남은 필름 : {st.session_state.remaining_films} / 5장 <br><span style='font-size:12px; color:gray;'>(※ 자정 미사용분 1장 영구 산화)</span></h4>", 
    unsafe_allow_html=True
)
st.divider()

# 필름 모두 소진 시 차단 로직
if st.session_state.remaining_films <= 0:
    st.error("🚨 오늘치 귀한 필름을 모두 소진하셨습니다! 내일 다시 찾아와주세요.")
    st.stop()

# --- 4. STEP 1: 테마 선택 및 사진 업로드 ---
if st.session_state.step == "select_theme":
    st.markdown("### 1. 어떤 감성으로 기록할까요?")
    theme = st.radio(
        "테마 선택 (포장지 변경)", 
        ["🕰️ 레트로 트래블 (인사동/데이트)", "🧸 꾸러기 스케치북 (키즈/장난감)", "🔥 커뮤니티 라이브 (단체 모임/공유)"]
    )
    
    st.markdown("### 2. 현장의 사진 5장을 선택해주세요")
    uploaded_files = st.file_uploader("사진을 이곳에 끌어다 놓으세요", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    user_text = st.text_input("✏️ 한 줄 추억 남기기 (최대 20자)", placeholder="예: 인사동 거리에서 우리의 첫 기록!")

    # 렌더링 시작 버튼
    if st.button("✨ 10초 영화 인화하기 (필름 1장 차감)", use_container_width=True):
        if len(uploaded_files) != 5:
            st.warning("⚠️ 정확히 5장의 사진을 올려주셔야 인화기가 작동합니다!")
        else:
            st.session_state.remaining_films -= 1
            st.session_state.step = "rendering"
            st.session_state.uploaded_files = uploaded_files
            st.session_state.user_text = user_text
            st.session_state.theme = theme
            st.rerun()

# --- 5. STEP 2: 렌더링 (인화 과정) ---
elif st.session_state.step == "rendering":
    st.info("기이이잉- 📸 디지털 인화 중입니다. 잠시만 기다려주세요...")
    progress_bar = st.progress(0)
    
    images = []
    # 5장 이미지 리사이징 및 텍스트 합성 처리
    for i, file in enumerate(st.session_state.uploaded_files):
        try:
            img = Image.open(file).convert("RGB")
            # 서버 과부하 방지를 위한 리사이징 (CTO 최적화)
            img = img.resize((400, 400)) 
            
            # 메타데이터 및 텍스트 모의 각인
            draw = ImageDraw.Draw(img)
            # 클라우드 기본 폰트 사용 (한글 깨짐 방지를 위해 영어/숫자 위주로 우선 배치)
            draw.text((10, 360), f"Memories in Seoul", fill="white")
            draw.text((10, 380), f"{datetime.now().strftime('%Y.%m.%d %H:%M')}", fill="white")
            
            images.append(img)
        except Exception as e:
            st.error("이미지 처리 중 오류가 발생했습니다. 다른 사진을 시도해주세요.")
            st.stop()
            
        time.sleep(0.5) # 인화되는 듯한 시각적 효과
        progress_bar.progress((i + 1) * 20)
        
    # 메모리상에서 GIF 굽기 (imageio 사용)
    gif_io = io.BytesIO()
    imageio.mimsave(gif_io, images, format='GIF', duration=500, loop=0)
    st.session_state.gif_bytes = gif_io.getvalue()
    
    st.session_state.step = "share"
    st.rerun()

# --- 6. STEP 3: 조급함 유발 (시간 압박 락인) ---
elif st.session_state.step == "share":
    st.success("🎉 인화 완료!")
    st.markdown(f"**선택된 테마:** {st.session_state.theme}")
    st.markdown(f"**나의 추억:** {st.session_state.user_text}")
    
    # 20초 압박 경고문
    st.error("⏳ **긴급! 20초 이내에 갤러리에 저장하거나 공유하지 않으면 결과물이 영구 증발합니다!**")
    
    # 결과물 출력
    st.image(st.session_state.gif_bytes, use_column_width=True)
    
    # 다운로드(공유) 버튼
    st.download_button(
        label="🚀 늦기 전에 내 폰에 저장 / 공유하기",
        data=st.session_state.gif_bytes,
        file_name="ai_polaroid_live.gif",
        mime="image/gif",
        use_container_width=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 새로운 필름 넣기 (처음으로)"):
        st.session_state.step = "select_theme"
        st.rerun()