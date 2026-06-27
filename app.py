import streamlit as st
import boto3
import uuid
import json
from PIL import Image, ImageOps
import io

# ==========================================
# [AI Pola] 메인 애플리케이션 소스 코드 (app.py)
# 모바일 회전 버그 해결 + 2~5장 업로드 + 최고 보안(Secrets) 적용판
# ==========================================

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="AI Pola - 10초 영화 인화 서비스",
    page_icon="🎬",
    layout="centered"
)

# 2. AWS 서비스 클라이언트 초기화 함수 (최고 보안 방식)
def get_aws_client(service_name):
    try:
        # st.secrets라는 튼튼한 금고에서 알아서 키를 꺼내옵니다.
        return boto3.client(
            service_name,
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
            aws_secret_access_key=st.secrets["AWS_SECRET_KEY"],
            region_name=st.secrets.get("AWS_REGION", "ap-northeast-2")
        )
    except Exception as e:
        st.error(f"서버 내부 통신 금고(Secrets) 연결 오류가 발생했습니다: {e}")
        return None

# 3. 무결성 이미지 처리 파이프라인 (가로/세로 회전 버그 완벽 차단)
def process_image_bulletproof(uploaded_file):
    img = Image.open(uploaded_file)
    
    # [핵심] 모바일 기기의 EXIF 회전 정보를 물리적으로 정정
    img = ImageOps.exif_transpose(img)
    
    # 포맷 강제 정규화 (PNG/RGBA 충돌 방지)
    if img.mode in ("RGBA", "P"):
        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            rgb_img.paste(img, mask=img.split()[3])
        else:
            rgb_img.paste(img)
        img = rgb_img
    elif img.mode != "RGB":
        img = img.convert("RGB")
    
    # 정중앙 1080x1080 크롭
    width, height = img.size
    min_dim = min(width, height)
    
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    
    img = img.crop((left, top, right, bottom))
    img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
    
    return img

def upload_image_to_s3(s3_client, img, bucket_name, s3_key):
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    s3_client.upload_fileobj(buffer, bucket_name, s3_key)

# 4. Streamlit 서비스 메인 UI
st.title("🎬 AI Pola")
st.subheader("10초 영화 인화 서비스")
st.write("업로드하신 사진을 왜곡 없는 정방형 레이아웃의 10초 영화 영상으로 구워냅니다.")

st.divider()

# 파일 업로더: 2장 ~ 5장 허용
uploaded_files = st.file_uploader(
    "영상으로 인화할 사진을 2~5장 업로드해주세요 (지원 포맷: JPG, JPEG, PNG)",
    accept_multiple_files=True,
    type=['jpg', 'jpeg', 'png']
)

if st.button("🚀 10초 영화 인화 시작", type="primary"):
    if not uploaded_files or not (2 <= len(uploaded_files) <= 5):
        st.error("❌ 안정적인 영상 생성을 위해 최소 2장부터 최대 5장까지의 사진을 업로드해주세요.")
    else:
        s3_client = get_aws_client('s3')
        sqs_client = get_aws_client('sqs')
        
        if s3_client and sqs_client:
            # 금고에서 버킷과 대기열 이름도 꺼내옵니다
           bucket_name = "aipola-temp-storage-1782548118"
            queue_url = "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue"
            request_id = str(uuid.uuid4())
            s3_keys = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 업로드된 사진 개수에 맞춰 진행률 100% 매끄럽게 처리
                total_files = len(uploaded_files)
                progress_step = 80 / total_files 
                
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"📷 {i+1}번째 이미지 규격 최적화 중...")
                    
                    processed_img = process_image_bulletproof(file)
                    s3_key = f"uploads/{request_id}/image_{i+1}.jpg"
                    
                    upload_image_to_s3(s3_client, processed_img, bucket_name, s3_key)
                    s3_keys.append(s3_key)
                    
                    current_progress = int((i + 1) * progress_step)
                    progress_bar.progress(current_progress)
                
                status_text.text("📨 최종 백엔드 인화 대기열에 등록 중...")
                message_payload = {
                    "request_id": request_id,
                    "s3_keys": s3_keys
                }
                
                sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(message_payload)
                )
                
                progress_bar.progress(100)
                status_text.empty()
                st.success(f"🎉 총 {total_files}장의 사진으로 10초 영화 인화 요청이 완료되었습니다!")
                st.balloons()
                
                st.info(
                    f"**인화 요청 ID:** `{request_id}`\n\n"
                    "시스템 내부에서 안전하게 영상 조립 작업을 수행하고 있습니다. 잠시만 기다려주세요."
                )
                
            except Exception as e:
                st.error(f"🚨 처리 중 내부 통신 오류가 발생했습니다: {e}")
