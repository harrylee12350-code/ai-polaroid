import streamlit as st
from PIL import Image, ImageOps
import io
import time

# 페이지 설정
st.set_page_config(page_title="AI 폴라로이드 스튜디오", layout="centered")

# --- UI 스타일 ---
st.markdown("""
    <style>
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; padding: 20px; }
    </style>
""", unsafe_allow_html=True)

# 1. 상단 타이틀
st.title("📸 AI 폴라로이드 스튜디오")

# 2. 메인 액션 영역
st.subheader("추억을 폴라로이드로 인화하세요")

# 파일 업로드 (최대 5장)
uploaded_files = st.file_uploader("최대 5장의 사진을 올려주세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    if len(uploaded_files) > 5:
        st.error("최대 5장까지만 가능합니다.")
    else:
        st.success(f"{len(uploaded_files)}장의 사진이 준비되었습니다.")
        
        # 렌더링 버튼
        if st.button("✨ 시네마틱 렌더링 시작"):
            
            # 여기서부터 실제 렌더링 로직이 시작됩니다.
            with st.spinner('시네마틱 렌더링 진행 중입니다... 잠시만 기다려주세요.'):
                frames = []
                
                # 1. 업로드된 사진들을 하나씩 꺼내서 가공
                for uploaded_file in uploaded_files:
                    img = Image.open(uploaded_file)
                    # 스마트폰 세로/가로 회전 자동 보정
                    img = ImageOps.exif_transpose(img)
                    # 영상을 만들기 위해 모든 사진의 크기를 600x600으로 통일
                    img = img.resize((600, 600))
                    frames.append(img)
                
                # 2. 결과물을 저장할 가상의 메모리 공간(버퍼) 생성
                output_buffer = io.BytesIO()
                
                # 3. 렌더링 (여러 장이면 GIF 애니메이션, 1장이면 일반 이미지)
                if len(frames) > 1:
                    frames[0].save(
                        output_buffer, 
                        format='GIF', 
                        save_all=True, 
                        append_images=frames[1:], 
                        duration=800, # 0.8초마다 사진 전환
                        loop=0
                    )
                    file_name = "cinematic_polaroid.gif"
                    mime_type = "image/gif"
                else:
                    frames[0].save(output_buffer, format='JPEG')
                    file_name = "cinematic_polaroid.jpg"
                    mime_type = "image/jpeg"
                
                # 4. 다운로드를 위해 버퍼의 읽기 위치를 처음으로 되돌림
                output_buffer.seek(0)
                
                # 시각적 효과를 위한 살짝의 딜레이
                time.sleep(1)
                
            # --- 렌더링 완료 및 UI 업데이트 ---
            st.success("✅ 렌더링이 완료되었습니다!")
            
            # 결과물 화면에 보여주기
            st.image(output_buffer, caption="완성된 시네마틱 결과물")
            
            # 5. 다운로드 버튼 (이제 진짜 메모리의 데이터가 파일로 저장됩니다)
            st.download_button(
                label="💾 갤러리에 저장하기", 
                data=output_buffer,
                file_name=file_name, 
                mime=mime_type
            )
            st.button("🔗 친구에게 공유하기")

# 3. 하단 리텐션 영역 (원스톱 서비스)
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.link_button("📖 효창공원 역사 보기", "https://example.com/history")
with col2:
    st.link_button("🍽️ 근처 맛집 추천 보기", "https://example.com/restaurants")