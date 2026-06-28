import streamlit as st
import boto3
import uuid
import json
from PIL import Image, ImageOps
import io
import os

# ==========================================
# [AI Pola] 메인 애플리케이션 소스 코드 (app.py)
# 모바일 회전 버그 해결 + 2~5장 업로드 + 클라우드(Railway) 완벽 호환판
# ==========================================

st.set_page_config(
    page_title="AI Pola - 10초 영화 인화 서비스",
    page_icon="🎬",
    layout="centered"
)

# 💡 [핵심 수정 1] st.secrets 완전 제거 및 환경변수(os.getenv) 단일화
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2")

# 💡 [핵심 수정 2] worker.py와 동일하게 기본 창고(Bucket)와 대기열(SQS) 주소 하드코딩 백업
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "aipola-temp-storage-1782548118")
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")

def get_aws_client(service_name):
    try:
        if AWS_ACCESS_KEY and AWS_SECRET_KEY:
            return boto3.client(
                service_name,
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
                region_name=AWS_REGION
            )
        else:
            return boto3.client(service_name, region_name=AWS_REGION)
    except Exception as e:
        st.error(f"서버 내부 연결 오류가 발생했습니다: {e}")
        return None

def process_image_bulletproof(uploaded_file):
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    
    if img.mode in ("RGBA", "P"):
        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            rgb_img.paste(img, mask=img.split()[3])
        else:
            rgb_img.paste(img)
        img = rgb_img
    elif img.mode != "RGB":
        img = img.convert("RGB")
    
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

st.title("🎬 AI Pola")
st.subheader("10초 영화 인화 서비스")
st.write("업로드하신 사진을 왜곡 없는 정방형 레이아웃의 10초 영화 영상으로 구워냅니다.")

st.divider()

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
            request_id = str(uuid.uuid4())
            s3_keys = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                total_files = len(uploaded_files)
                progress_step = 80 / total_files 
                
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"📷 {i+1}번째 이미지 규격 최적화 중...")
                    
                    processed_img = process_image_bulletproof(file)
                    s3_key = f"uploads/{request_id}/image_{i+1}.jpg"
                    
                    upload_image_to_s3(s3_client, processed_img, S3_BUCKET, s3_key)
                    s3_keys.append(s3_key)
                    
                    current_progress = int((i + 1) * progress_step)
                    progress_bar.progress(current_progress)
                
                status_text.text("📨 최종 백엔드 인화 대기열에 등록 중...")
                message_payload = {
                    "request_id": request_id,
                    "s3_keys": s3_keys
                }
                
                sqs_client.send_message(
                    QueueUrl=SQS_URL,
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