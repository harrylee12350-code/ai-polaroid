import streamlit as st
import boto3
import os
import json
import uuid
import time
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "ap-northeast-2"

S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")

aws_credentials = {"region_name": AWS_REGION}
if AWS_ACCESS_KEY and AWS_SECRET_KEY:
    aws_credentials["aws_access_key_id"] = AWS_ACCESS_KEY
    aws_credentials["aws_secret_access_key"] = AWS_SECRET_KEY

s3 = boto3.client('s3', **aws_credentials)
sqs = boto3.client('sqs', **aws_credentials)

st.set_page_config(page_title="AI Pola", page_icon="🎬")
st.title("🎬 AI Pola - 10초 영화 인화 서비스")
st.write("---")

uploaded_files = st.file_uploader("영상으로 인화할 사진을 2~5장 업로드해주세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if st.button("🚀 10초 영화 인화 시작"):
    if not uploaded_files:
        st.warning("사진을 업로드해주세요!")
    elif len(uploaded_files) < 2 or len(uploaded_files) > 5:
        st.error("사진은 2장 이상, 5장 이하로 업로드해주세요.")
    else:
        request_id = str(uuid.uuid4())
        s3_keys = []
        
        for i, file in enumerate(uploaded_files):
            st.info(f"📷 {i+1}번째 이미지 업로드 중...")
            file_ext = file.name.split('.')[-1]
            s3_key = f"uploads/{request_id}/image_{i+1}.{file_ext}"
            s3.upload_fileobj(file, S3_BUCKET, s3_key)
            s3_keys.append(s3_key)
        
        order_payload = {"request_id": request_id, "s3_keys": s3_keys}
        sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(order_payload))
        
        with st.spinner("🎬 영화를 초고속 인화 중입니다! 잠시만 기다려주세요...⏳"):
            s3_gif_key = f"rendered/{request_id}.gif"
            max_retries = 30  # 초고속 가동이므로 1분이면 넉넉합니다.
            gif_ready = False
            
            for _ in range(max_retries):
                try:
                    s3.head_object(Bucket=S3_BUCKET, Key=s3_gif_key)
                    gif_ready = True
                    break
                except:
                    time.sleep(2)
            
            if gif_ready:
                st.balloons()
                st.success("✨ 영화 인화가 완료되었습니다!")
                
                # 화면에 GIF 표출
                gif_url = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': s3_gif_key}, ExpiresIn=3600)
                st.image(gif_url, use_container_width=True)
                
                # 저장 및 보내기용 다운로드 버튼 (필수 기능)
                gif_obj = s3.get_object(Bucket=S3_BUCKET, Key=s3_gif_key)
                gif_bytes = gif_obj['Body'].read()
                
                st.download_button(
                    label="💾 내 폰에 영화 저장하기 (공유 가능)",
                    data=gif_bytes,
                    file_name="AI_Pola_Movie.gif",
                    mime="image/gif"
                )
            else:
                st.error("서버 정체로 처리가 지연되었습니다. 잠시 후 다시 시도해주세요.")