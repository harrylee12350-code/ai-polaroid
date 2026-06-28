import streamlit as st
import boto3
import os
import json
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "ap-northeast-2"
S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")

# AWS 인증
aws_credentials = {"region_name": AWS_REGION}
if AWS_ACCESS_KEY and AWS_SECRET_ACCESS_KEY:
    aws_credentials["aws_access_key_id"] = AWS_ACCESS_KEY
    aws_credentials["aws_secret_access_key"] = AWS_SECRET_ACCESS_KEY

s3 = boto3.client('s3', **aws_credentials)
sqs = boto3.client('sqs', **aws_credentials)

st.set_page_config(page_title="찰나 (Chalna)", page_icon="🎬", layout="centered")

# 2. UI 레이아웃
mode = st.radio("서비스 모드를 선택해 주세요", ["일반 모드 (상세 기록)", "👶 아기 모드 (간편 기록)"], horizontal=True)
st.write("---")

if mode == "👶 아기 모드 (간편 기록)":
    st.title("👶 찰나 - 우리 아기 감성 폴라로이드")
    # 💡 [개선] 기본값 '우리집' 세팅, 필요시 수정 가능하도록 설계
    place_str = st.text_input("장소", value="우리집")
    message_str = st.selectbox("할머니, 부모님께 보낼 예쁜 마음", ["사랑해요!", "오늘의 나예요!", "보고 싶어요!", "많이 자랐죠?", "씽긋 웃는 찰나!"])
    date_str = datetime.now().strftime("%Y.%m.%d")
else:
    st.title("🎬 찰나 - 당신의 순간을 영화로")
    selected_date = st.date_input("추억의 날짜", datetime.now())
    date_str = selected_date.strftime("%Y.%m.%d")
    place_str = st.text_input("추억의 장소", placeholder="예: 한강공원")
    message_str = st.text_input("나만의 멘트 (20자 이내)", max_chars=20)

uploaded_files = st.file_uploader("사진 2~5장 업로드", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# 3. 인화 처리 로직
if st.button("🚀 찰나 영화 인화 시작"):
    if not uploaded_files:
        st.warning("사진을 업로드해 주세요!")
    elif len(uploaded_files) < 2 or len(uploaded_files) > 5:
        st.error("사진은 2~5장 업로드 가능합니다.")
    else:
        request_id = str(uuid.uuid4())
        s3_keys = []
        for i, file in enumerate(uploaded_files):
            file_ext = file.name.split('.')[-1]
            s3_key = f"uploads/{request_id}/image_{i+1}.{file_ext}"
            s3.upload_fileobj(file, S3_BUCKET, s3_key)
            s3_keys.append(s3_key)
        
        order_payload = {
            "request_id": request_id,
            "s3_keys": s3_keys,
            "meta": {"date": date_str, "place": place_str, "message": message_str}
        }
        
        sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(order_payload))
        
        with st.spinner("🎬 폴라로이드 텍스트 정밀 인화 중..."):
            s3_gif_key = f"rendered/{request_id}.gif"
            gif_ready = False
            for _ in range(45):
                try:
                    s3.head_object(Bucket=S3_BUCKET, Key=s3_gif_key)
                    gif_ready = True
                    break
                except: time.sleep(2)
            
            if gif_ready:
                gif_url = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': s3_gif_key}, ExpiresIn=3600)
                st.image(gif_url, use_container_width=True)
                gif_bytes = s3.get_object(Bucket=S3_BUCKET, Key=s3_gif_key)['Body'].read()
                st.download_button("💾 내 폰에 영화 저장하기", data=gif_bytes, file_name=f"Chalna_{date_str}.gif", mime="image/gif")
            else:
                st.error("인화가 지연되고 있습니다. 잠시 후 다시 시도해 주세요.")