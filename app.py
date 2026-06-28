import streamlit as st
import boto3
import os
import json
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv

# 1. 환경 변수 로드 및 AWS 기본 세팅
load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "ap-northeast-2"

S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")

# AWS 인증 정보 설정
aws_credentials = {"region_name": AWS_REGION}
if AWS_ACCESS_KEY and AWS_SECRET_ACCESS_KEY:
    aws_credentials["aws_access_key_id"] = AWS_ACCESS_KEY
    aws_credentials["aws_secret_access_key"] = AWS_SECRET_ACCESS_KEY

s3 = boto3.client('s3', **aws_credentials)
sqs = boto3.client('sqs', **aws_credentials)

# 2. 웹사이트 기본 스타일 및 브랜딩 세팅
st.set_page_config(page_title="찰나 (Chalna)", page_icon="🎬", layout="centered")

# 유아용/일반용 모드 스위치 (폰에서도 누르기 쉽게 상단 배치)
mode = st.radio("서비스 모드를 선택해 주세요", ["일반 모드 (상세 기록)", "👶 아기 모드 (간편 기록)"], horizontal=True)
st.write("---")

# 3. 모드별 맞춤형 UI 분리 레이아웃
if mode == "👶 아기 모드 (간편 기록)":
    st.title("👶 찰나 - 우리 아기 감성 폴라로이드")
    st.write("글자를 몰라도 괜찮아요! 사진을 고르고 엄마, 할머니에게 보낼 예쁜 문구 버튼을 눌러보세요.")
    
    # 아기 모드는 날짜와 장소를 자동으로 셋팅해 폰 입력을 최소화합니다.
    date_str = datetime.now().strftime("%Y.%m.%d")
    place_str = "우리집"
    
    # 아기들이 터치하기 쉬운 자동 완성 추천 멘트 구성
    baby_preset = st.selectbox(
        "할머니, 부모님께 보낼 예쁜 마음을 골라보세요", 
        ["사랑해요!", "오늘의 나예요!", "보고 싶어요!", "많이 자랐죠?", "씽긋 웃는 찰나!"]
    )
    message_str = baby_preset

else:
    st.title("🎬 찰나 - 당신의 순간을 영화로")
    st.write("폴라로이드 감성 테두리 위에 박제될 날짜, 장소, 그리고 20자 이내의 추억을 기록해 보세요.")
    
    # 일반 모드는 상세 기입창을 열어줍니다.
    selected_date = st.date_input("추억의 날짜", datetime.now())
    date_str = selected_date.strftime("%Y.%m.%d")
    
    place_str = st.text_input("추억의 장소", placeholder="예: 한강공원, 남해바다")
    message_str = st.text_input("나만의 멘트 기입 (최대 20자)", max_chars=20, placeholder="예: 함께해서 행복했던 날")

# 4. 이미지 업로드 창 (2~5장 방어막 유지)
st.write("")
uploaded_files = st.file_uploader("영상으로 인화할 사진을 2~5장 선택해 주세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# 5. 인화 가동 작동 버튼
if st.button("🚀 찰나 영화 인화 시작"):
    if not uploaded_files:
        st.warning("사진을 업로드해 주세요!")
    elif len(uploaded_files) < 2 or len(uploaded_files) > 5:
        st.error("사진은 최소 2장, 최대 5장까지만 업로드 가능합니다.")
    else:
        # 고유 주문 번호표 발급
        request_id = str(uuid.uuid4())
        s3_keys = []
        
        # [STEP 1] 원본 사진 S3 창고로 업로드
        for i, file in enumerate(uploaded_files):
            st.info(f"📷 {i+1}번째 사진 규격 최적화 및 업로드 중...")
            file_ext = file.name.split('.')[-1]
            s3_key = f"uploads/{request_id}/image_{i+1}.{file_ext}"
            s3.upload_fileobj(file, S3_BUCKET, s3_key)
            s3_keys.append(s3_key)
        
        # [STEP 2] 뒷방 공장(worker.py)으로 보낼 완성형 주문서 포장
        # 💡 대표님이 기획하신 meta 데이터(날짜, 장소, 멘트)를 주문서에 완벽히 동봉합니다!
        order_payload = {
            "request_id": request_id,
            "s3_keys": s3_keys,
            "meta": {
                "date": date_str,
                "place": place_str,
                "message": message_str
            }
        }
        
        # 주문서를 SQS 대기열 링크로 발송
        sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(order_payload))
        
        # [STEP 3] 공장에서 완성품(.gif)이 S3 창고에 배달될 때까지 화면 홀딩 대기
        with st.spinner("🎬 찰나 공장에서 필름을 현상하고 폴라로이드 텍스트를 정밀 인화하고 있습니다...⏳"):
            s3_gif_key = f"rendered/{request_id}.gif"
            max_retries = 45  # 2초씩 45번 = 총 90초 대기 방어막 설정
            gif_ready = False
            
            for _ in range(max_retries):
                try:
                    # S3 창고에 완성이 되었는지 똑똑 노크
                    s3.head_object(Bucket=S3_BUCKET, Key=s3_gif_key)
                    gif_ready = True
                    break
                except:
                    time.sleep(2)  # 아직 조리 중이면 2초 쉬고 다시 노크
            
            # [STEP 4] 완성 시 결과물 송출 및 저장 버튼 활성화
            if gif_ready:
                st.balloons()
                st.success("✨ 세상에 단 하나뿐인 '찰나' 폴라로이드 영화가 완성되었습니다!")
                
                # 유저 폰 브라우저용 스트리밍 안전 주소 생성
                gif_url = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': s3_gif_key}, ExpiresIn=3600)
                
                # 가로세로 절대 찌그러지지 않는 캔버스 이미지 스크린 표출
                st.image(gif_url, use_container_width=True)
                
                # 갤러리 저장 및 가족 카톡방 공유(보내기)를 위한 바이럴 파일 추출
                gif_obj = s3.get_object(Bucket=S3_BUCKET, Key=s3_gif_key)
                gif_bytes = gif_obj['Body'].read()
                
                st.write("")
                st.download_button(
                    label="💾 내 폰에 영화 저장하기 (카톡 공유 가능)",
                    data=gif_bytes,
                    file_name=f"Chalna_{date_str}.gif",
                    mime="image/gif"
                )
            else:
                st.error("현재 주문 폭주로 인화가 지연되고 있습니다. 잠시 후 새로고침하여 다시 시도해 주세요.")