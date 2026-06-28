import streamlit as st
import boto3
import os
import json
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv

# 1. 설정 및 인증 (오류 방지)
load_dotenv()
S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")

# S3/SQS 클라이언트 초기화
s3 = boto3.client('s3', region_name="ap-northeast-2")
sqs = boto3.client('sqs', region_name="ap-northeast-2")

st.set_page_config(page_title="찰나 (Chalna)", page_icon="🎬", layout="centered")

# 2. UI 및 모드별 로직
mode = st.radio("서비스 모드를 선택해 주세요", ["일반 모드 (상세 기록)", "👶 아기 모드 (간편 기록)"], horizontal=True)
st.write("---")

# 연령대별 추천 문구 프리셋
presets = {
    "신생아(0~1세)": ["천사 같은 우리 아기", "건강하게 자라렴", "사랑해요, 아가야"],
    "영유아(2~3세)": ["오늘도 무럭무럭!", "어디든 찰나!", "귀염둥이 성장 중"],
    "유아(4~5세)": ["벌써 이렇게 컸네!", "사랑스러운 내 보물", "최고의 찰나!"]
}

if mode == "👶 아기 모드 (간편 기록)":
    st.title("👶 찰나 - 우리 아기 감성 폴라로이드")
    age_group = st.selectbox("아기 연령대를 선택하세요", list(presets.keys()))
    place_str = st.text_input("장소", value="우리집")
    message_str = st.selectbox("할머니, 부모님께 보낼 예쁜 마음", presets[age_group])
    date_str = datetime.now().strftime("%Y.%m.%d")
else:
    st.title("🎬 찰나 - 당신의 순간을 영화로")
    selected_date = st.date_input("추억의 날짜", datetime.now())
    date_str = selected_date.strftime("%Y.%m.%d")
    place_str = st.text_input("추억의 장소", placeholder="예: 한강공원")
    message_str = st.text_input("나만의 멘트 (20자 이내)", max_chars=20)

uploaded_files = st.file_uploader("사진 2~5장 업로드", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# 3. 인화 처리 (안정성 강화)
if st.button("🚀 찰나 영화 인화 시작"):
    if not uploaded_files:
        st.warning("사진을 업로드해 주세요!")
    elif not (2 <= len(uploaded_files) <= 5):
        st.error("사진은 2~5장 업로드 가능합니다.")
    else:
        try:
            request_id = str(uuid.uuid4())
            s3_keys = []
            
            # S3 업로드 루프
            for i, file in enumerate(uploaded_files):
                ext = file.name.split('.')[-1]
                key = f"uploads/{request_id}/image_{i+1}.{ext}"
                s3.upload_fileobj(file, S3_BUCKET, key)
                s3_keys.append(key)
            
            # 큐 전달
            payload = {
                "request_id": request_id, 
                "s3_keys": s3_keys, 
                "meta": {"date": date_str, "place": place_str, "message": message_str}
            }
            sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(payload))
            
            # 렌더링 대기 처리 (폴링)
            with st.spinner("🎬 찰나 영화 인화 중... 잠시만 기다려 주세요!"):
                s3_gif_key = f"rendered/{request_id}.gif"
                for _ in range(30):
                    try:
                        s3.head_object(Bucket=S3_BUCKET, Key=s3_gif_key)
                        gif_ready = True
                        break
                    except:
                        time.sleep(2)
                else:
                    gif_ready = False
            
            if gif_ready:
                gif_url = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': s3_gif_key}, ExpiresIn=3600)
                st.image(gif_url, use_container_width=True)
                gif_bytes = s3.get_object(Bucket=S3_BUCKET, Key=s3_gif_key)['Body'].read()
                st.download_button("💾 내 폰에 영화 저장하기", data=gif_bytes, file_name=f"Chalna_{date_str}.gif", mime="image/gif")
            else:
                st.error("인화 서버가 바쁩니다. 잠시 후 '인화 시작' 버튼을 다시 눌러주세요.")
                
        except Exception as e:
            st.error(f"시스템 에러 발생: {e}")