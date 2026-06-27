import streamlit as st
import boto3
import uuid
import json
from PIL import Image, ImageOps
import io
import os

# ==========================================
# [AI Pola] 메인 애플리케이션 소스 코드 (app.py)
# 2~5장 유동적 업로드 + 자동 연결 복구 + 모바일 회전 버그 수정판
# ==========================================

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="AI Pola - 10초 영화 인화 서비스",
    page_icon="🎬",
    layout="centered"
)

# 2. AWS 서비스 클라이언트 초기화 함수 (이전 MVP 자동 인식 방식으로 원상복구)
def get_aws_client(service_name):
    # 개발자가 추가했던 불필요한 st.secrets 에러 유발 코드를 삭제했습니다.
    # 이전처럼 Streamlit Cloud의 기본 환경을 이용해 알아서 연결됩니다.
    try:
        return boto3.client(service_name, region_name="ap-northeast-2")
    except Exception as e:
        st.error(f"서버 내부 통신 오류가 발생했습니다: {e}")
        return None

# 3. 무결성 이미지 처리 파이프라인 (가로/세로 회전 버그 해결)
def process_image_bulletproof(uploaded_file):
    img = Image.open(uploaded_file)
    
    # [핵심] 모바일 기기의 EXIF 회전 정보를 물리적으로 정정
    img = ImageOps.exif_transpose(img)
    
    # 투명도가 있는 이미지(PNG 등)가 JPEG로 변환될 때 깨지는 현상 방지
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

# (에러 수정) 파일 업로더: 2장 ~ 5장 허용
uploaded_files = st.file_uploader(
    "영상으로 인화할 사진을 2~5장 업로드해주세요 (지원 포맷: JPG, JPEG, PNG)",
    accept_multiple_files=True,
    type=['jpg', 'jpeg', 'png']
)

if st.button("🚀 10초 영화 인화 시작", type="primary"):
    # 2장 미만, 5장 초과일 때만 막기
    if not uploaded_files or not (2 <= len(uploaded_files) <= 5):
        st.error("❌ 안정적인 영상 생성을 위해 최소 2장부터 최대 5장까지의 사진을 업로드해주세요.")
    else:
        # 원래 방식대로 조용히 클라이언트 연결
        s3_client = get_aws_client('s3')
        sqs_client = get_aws_client('sqs')
        
        if s3_client and sqs_client:
            # 기존 MVP 서버에 등록되어 있던 환경 변수명을 그대로 끌어옵니다
            bucket_name = os.environ.get("S3_BUCKET_NAME", "ai-pola-bucket")
            queue_url = os.environ.get("SQS_QUEUE_URL", "ai-pola-queue")
            
            request_id = str(uuid.uuid4())
            s3_keys = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 업로드된 사진 개수(N)에 맞춰 진행률 100%를 N등분하여 부드럽게 채움
                total_files = len(uploaded_files)
                progress_step = 80 / total_files  # 업로드 과정이 전체의 80% 차지
                
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