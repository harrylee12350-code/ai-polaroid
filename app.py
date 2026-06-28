import streamlit as st
import boto3
import os
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

# 💡 [핵심 수정] Secrets 수첩 대신 Railway 환경 변수를 바로 바라보도록 고정
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "ap-northeast-2"

# 💡 [핵심 수정] 공장(worker.py)과 정확히 일치하는 S3 창고 주소와 SQS 주문서 주소 매핑
S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")

# AWS 클라이언트 안전하게 연결
aws_credentials = {
    "region_name": AWS_REGION
}
if AWS_ACCESS_KEY and AWS_SECRET_KEY:
    aws_credentials["aws_access_key_id"] = AWS_ACCESS_KEY
    aws_credentials["aws_secret_access_key"] = AWS_SECRET_KEY

s3 = boto3.client('s3', **aws_credentials)
sqs = boto3.client('sqs', **aws_credentials)

# --- 웹사이트 화면 UI 구성 ---
st.title("🎬 AI Pola - 10초 영화 인화 서비스")
st.write("---")

uploaded_files = st.file_uploader(
    "영상으로 인화할 사진을 2~5장 업로드해주세요 (지원 포맷: JPG, JPEG, PNG)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if st.button("🚀 10초 영화 인화 시작"):
    if not uploaded_files:
        st.warning("사진을 업로드해주세요!")
    elif len(uploaded_files) < 2 or len(uploaded_files) > 5:
        st.error("사진은 2장 이상, 5장 이하로 업로드해주세요.")
    else:
        try:
            request_id = str(uuid.uuid4())
            s3_keys = []
            
            # 1. 파일 처리 및 S3 업로드
            for i, file in enumerate(uploaded_files):
                st.info(f"📷 {i+1}번째 이미지 규격 최적화 중...")
                
                file_ext = file.name.split('.')[-1]
                s3_key = f"uploads/{request_id}/image_{i+1}.{file_ext}"
                
                # AWS S3 창고로 사진 전송
                s3.upload_fileobj(file, S3_BUCKET, s3_key)
                s3_keys.append(s3_key)
            
            st.success("📸 모든 사진이 S3 창고에 안전하게 저장되었습니다!")
            
            # 2. SQS 주문서 작성 및 전송 (공장이 읽을 수 있는 리스트 형식으로 포맷 통일)
            st.info("📨 렌더링 공장에 주문서 전송 중...")
            order_payload = {
                "request_id": request_id,
                "s3_keys": s3_keys
            }
            
            sqs.send_message(
                QueueUrl=SQS_URL,
                MessageBody=json.dumps(order_payload)
            )
            
            st.balloons()
            st.success("🎉 주문 완료! 뒷방 렌더링 공장이 영상을 제작하기 시작했습니다. 잠시만 기다려주세요!")
            
        except Exception as e:
            st.error(f"서버 내부 통신 금고(Secrets) 연결 오류가 발생했습니다: {e}")