import streamlit as st
import boto3
import uuid
import json
from PIL import Image, ImageOps
import io

# ==========================================
# [AI Pola] 메인 애플리케이션 소스 코드 (app.py)
# 기기별 가로/세로 회전 무시 버그 및 포맷 충돌 완벽 수정판
# ==========================================

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="AI Pola - 10초 영화 인화 서비스",
    page_icon="🎬",
    layout="centered"
)

# 2. AWS 서비스 클라이언트 초기화 함수
def get_aws_client(service_name):
    try:
        return boto3.client(
            service_name,
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
            aws_secret_access_key=st.secrets["AWS_SECRET_KEY"],
            region_name=st.secrets.get("AWS_REGION", "ap-northeast-2")
        )
    except Exception as e:
        st.error(f"AWS 클라이언트 초기화 실패 ({service_name}): {e}")
        return None

# 3. 무결성 이미지 처리 파이프라인 (사이드 이펙트 원천 차단)
def process_image_bulletproof(uploaded_file):
    """
    모바일 기기의 EXIF Orientation 태그 오류를 물리적으로 정정하고,
    RGBA/P 포맷의 JPEG 저장 충돌을 방지하며, 정방향 1080x1080 센터 크롭을 수행합니다.
    """
    # 1단계: 이미지 바이너리 로드
    img = Image.open(uploaded_file)
    
    # 2단계: EXIF 메타데이터 기반 물리적 회전 적용 (가로/세로 뒤죽박죽 버그 해결 핵심)
    # 이 함수가 실행되면 이미지 픽셀 자체가 정방향으로 재배치되고 간섭 태그는 제거됩니다.
    img = ImageOps.exif_transpose(img)
    
    # 3단계: 포맷 안전성 확보 (사이드 이펙트 방지)
    # 아이폰 스크린샷이나 투명도가 포함된 PNG(RGBA, P 모드)를 JPEG로 변환할 때 발생하는 크래시 차단
    if img.mode in ("RGBA", "P"):
        # 투명 배경 영역이 검은색으로 깨지는 현상을 방지하기 위해 흰색 도화지 생성 후 합성
        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            rgb_img.paste(img, mask=img.split()[3])  # 3번째 인덱스가 알파(투명도) 채널
        else:
            rgb_img.paste(img)
        img = rgb_img
    elif img.mode != "RGB":
        img = img.convert("RGB")
    
    # 4단계: 완벽하게 정형화된 이미지 기준 정중앙 크롭 해상도 계산
    width, height = img.size
    min_dim = min(width, height)
    
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    
    # 정중앙 사각형 크롭 및 고화질 1080x1080 리사이징
    img = img.crop((left, top, right, bottom))
    img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
    
    return img

# 4. S3 업로드 유틸리티
def upload_image_to_s3(s3_client, img, bucket_name, s3_key):
    buffer = io.BytesIO()
    # 압축 품질 95%로 지정하여 이미지 손실 최소화 및 무결성 유지
    img.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    s3_client.upload_fileobj(buffer, bucket_name, s3_key)

# 5. Streamlit 서비스 메인 UI
st.title("🎬 AI Pola")
st.subheader("10초 영화 인화 서비스")
st.write("업로드하신 5장의 사진을 왜곡 없는 정방형 레이아웃의 10초 영화 영상으로 구워냅니다.")

st.divider()

# 파일 업로더 구성
uploaded_files = st.file_uploader(
    "영상으로 인화할 사진 5장을 한 번에 업로드해주세요 (지원 포맷: JPG, JPEG, PNG)",
    accept_multiple_files=True,
    type=['jpg', 'jpeg', 'png']
)

# 비동기 인화 프로세스 작동 버튼
if st.button("🚀 10초 영화 인화 시작", type="primary"):
    if not uploaded_files or len(uploaded_files) != 5:
        st.error("❌ 안정적인 영상 생성을 위해 정확히 5장의 사진을 고르고 업로드해주세요.")
    else:
        # AWS 클라이언트 세션 확보
        s3_client = get_aws_client('s3')
        sqs_client = get_aws_client('sqs')
        
        if s3_client and sqs_client:
            bucket_name = st.secrets["S3_BUCKET_NAME"]
            queue_url = st.secrets["SQS_QUEUE_URL"]
            
            # 병렬 요청 데이터 격리를 위한 고유 UUID 생성
            request_id = str(uuid.uuid4())
            s3_keys = []
            
            # 직관적인 UI 진행률 바 제공
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 5장의 이미지 순차 파이프라인 처리
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"📷 {i+1}번째 이미지의 모바일 회전 각도 교정 및 정방형 크롭 중...")
                    
                    # 결함 없는 무결성 이미지 변환
                    processed_img = process_image_bulletproof(file)
                    
                    # 고유 경로 지정을 위한 S3 키 포맷팅
                    s3_key = f"uploads/{request_id}/image_{i+1}.jpg"
                    
                    # S3 스토리지에 최종 물리 본 업로드
                    upload_image_to_s3(s3_client, processed_img, bucket_name, s3_key)
                    s3_keys.append(s3_key)
                    
                    # 전체 프로세스의 75% 영역을 업로드 진행률로 매핑
                    progress_bar.progress(int((i + 1) * 15))
                
                # SQS 비동기 대기열 메시지 페이로드 구성
                status_text.text("📨 비동기 백엔드 렌더링 대기열(SQS)에 인화 작업 등록 중...")
                message_payload = {
                    "request_id": request_id,
                    "s3_keys": s3_keys
                }
                
                sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(message_payload)
                )
                
                # 처리 완료 상태 업데이트
                progress_bar.progress(100)
                status_text.empty()
                st.success("🎉 10초 영화 인화 요청이 완벽하게 접수되었습니다!")
                st.balloons()
                
                st.info(
                    f"**인화 요청 ID:** `{request_id}`\n\n"
                    "현재 백엔드 인코더 시스템이 20초 제한 예외 처리 스케줄러 내부에서 안전하게 작업을 수행하고 있습니다. 영상 조립이 완료되면 즉시 전달됩니다."
                )
                
            except Exception as e:
                st.error(f"🚨 파이프라인 처리 중 치명적인 내부 오류가 발생했습니다: {e}")