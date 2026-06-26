import streamlit as st
from PIL import Image, ImageOps, ImageDraw
import io
import time
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="AI 폴라로이드 스튜디오", layout="centered")

# --- UI 스타일 ---
st.markdown("""
    <style>
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; padding: 20px; }
    stTextInput>div>div>input { font-size: 16px !important; }
    </style>
""", unsafe_allow_html=True)

# 1. 상단 타이틀
st.title("📸 AI 폴라로이드 스튜디오")

# 2. 메인 액션 영역
st.subheader("추억을 폴라로이드로 인화하세요")

# [UX 업그레이드] 유저 추억 입력 기록란 (최대 20자 제한)
user_memo = st.text_input(
    "✍️ 폴라로이드 하단에 새길 추억을 적어주세요 (최대 20자)", 
    max_chars=20,
    placeholder="예) 인사동에서 즐거운 데이트!"
)

# 파일 업로드 (최대 5장)
uploaded_files = st.file_uploader("최대 5장의 사진을 올려주세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    if len(uploaded_files) > 5:
        st.error("최대 5장까지만 가능합니다.")
    else:
        st.success(f"{len(uploaded_files)}장의 사진이 준비되었습니다.")
        
        # 렌더링 버튼
        if st.button("✨ 시네마틱 렌더링 시작"):
            
            with st.spinner('디지털 인화 및 시네마틱 렌더링 중...'):
                frames = []
                
                # 자동 기록용 데이터 생성 (현재 시간 및 필드 테스트 장소)
                current_time = datetime.now().strftime("%Y.%m.%d %H:%M")
                location_text = "📍 서울 인사동 (Insadong)"
                
                # 1. 업로드된 사진들을 하나씩 꺼내서 폴라로이드 감성으로 가공
                for uploaded_file in uploaded_files:
                    raw_img = Image.open(uploaded_file)
                    raw_img = ImageOps.exif_transpose(raw_img)
                    
                    # 사진 본체를 정방형(500x500)으로 크기 조절
                    photo = raw_img.resize((500, 500))
                    
                    # [CTO 재량 포장지] 폴라로이드 필름지 베이스 생성 (따뜻한 아이보리 색상, 560x680)
                    polaroid = Image.new("RGB", (560, 680), "#FDFBF7")
                    
                    # 필름지 상단에 사진 붙이기 (좌우 여백 30 픽셀, 상단 여백 30 픽셀)
                    polaroid.paste(photo, (30, 30))
                    
                    # 필름지 하단 여백에 글씨 새기기 (Digital Drawing)
                    draw = ImageDraw.Draw(polaroid)
                    
                    # 메타데이터 자동 각인 (날짜 및 장소) - 하단 좌측
                    draw.text((30, 550), f"{current_time} | {location_text}", fill="#888888")
                    
                    # 유저가 입력한 추억 한 줄 각인 - 하단 중앙부
                    if user_memo:
                        draw.text((30, 590), f"\"{user_memo}\"", fill="#111111")
                    else:
                        draw.text((30, 590), "\"기억하고 싶은 순간\"", fill="#aaaaaa")
                        
                    frames.append(polaroid)
                
                # 2. 결과물을 저장할 가상의 메모리 공간(버퍼) 생성
                output_buffer = io.BytesIO()
                
                # 3. 렌더링 (여러 장이면 GIF 애니메이션, 1장이면 일반 이미지)
                if len(frames) > 1:
                    frames[0].save(
                        output_buffer, 
                        format='GIF', 
                        save_all=True, 
                        append_images=frames[1:], 
                        duration=1000, # 필드 테스트 리액션을 위해 1초로 변경
                        loop=0
                    )
                    file_name = "cinematic_polaroid.gif"
                    mime_type = "image/gif"
                else:
                    frames[0].save(output_buffer, format='JPEG')
                    file_name = "cinematic_polaroid.jpg"
                    mime_type = "image/jpeg"
                
                output_buffer.seek(0)
                time.sleep(1.2) # 시네마틱 감성을 위한 약간의 대기 시간
                
            # --- 렌더링 완료 및 UI 업데이트 ---
            st.success("✅ 디지털 인화가 완료되었습니다!")
            
            # 결과물 화면에 미리보기 출력
            st.image(output_buffer, caption="완성된 디지털 폴라로이드 기록지")
            
            # 5. 다운로드 버튼
            st.download_button(
                label="💾 갤러리에 저장하기", 
                data=output_buffer,
                file_name=file_name, 
                mime=mime_type
            )
            st.button("🔗 친구에게 공유하기")

# 3. 하단 리텐션 영역 (원스톱 서비스)
st.markdown("---")
col1, col2 = col1, col2 = st.columns(2)
with col1:
    st.link_button("📖 효창공원 역사 보기", "https://example.com/history")
with col2:
    st.link_button("🍽️ 근처 맛집 추천 보기", "https://example.com/restaurants")