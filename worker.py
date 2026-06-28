import os
import time
import json
import uuid
import boto3
from PIL import Image, ImageOps, ImageDraw, ImageFont
from dotenv import load_dotenv

# 1. 환경 변수 로드 및 AWS 기본 세팅
load_dotenv()

S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")
AWS_REGION = "ap-northeast-2"

s3 = boto3.client('s3', region_name=AWS_REGION)
sqs = boto3.client('sqs', region_name=AWS_REGION)

def make_light_gif(image_paths, output_path, meta):
    print(f"🎬 비율 유지 & 텍스트 정밀 인화 시작: {meta}")
    
    raw_imgs = []
    for path in image_paths:
        img = Image.open(path)
        # 스마트폰 사진 회전 꼬리표(EXIF) 해결
        img = ImageOps.exif_transpose(img)
        # 4K 고화질 사진 초경량 다이어트 압축
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        raw_imgs.append(img)
    
    # 첫 번째 압축 이미지 크기를 기준으로 기준 해상도 설정
    target_w, target_h = raw_imgs[0].size
    
    # 시스템 폰트 로드 (에러 방지용 예외처리)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except:
        font = ImageFont.load_default()
    
    img_list = []
    for img in raw_imgs:
        # 1. 사진 비율 유지하며 하얀색 배경 바탕에 패딩 조립
        padded_img = ImageOps.pad(img, (target_w, target_h), color='white')
        
        # 2. 💡 폴라로이드 감성 하단 테두리 여백 확보 (세로로 140픽셀 추가 확장)
        canvas = Image.new("RGB", (target_w, target_h + 140), "white")
        canvas.paste(padded_img, (0, 0))
        
        # 3. 💡 대표님이 지시하신 날짜, 장소, 20자 멘트를 폴라로이드 테두리에 각인
        draw = ImageDraw.Draw(canvas)
        date_str = meta.get('date', '')
        place_str = meta.get('place', '')
        msg_str = meta.get('message', '')
        
        # 첫 줄: 날짜와 장소 / 둘째 줄: 나만의 감성 멘트
        text_line1 = f"📅 {date_str}  |  📍 {place_str}"
        text_line2 = f"✍️ {msg_str}"
        
        draw.text((30, target_h + 20), text_line1, fill="#333333", font=font)
        draw.text((30, target_h + 70), text_line2, fill="#111111", font=font)
        
        img_list.append(canvas)
    
    # 2초 단위 무한 반복 초경량 GIF 저장
    img_list[0].save(
        output_path,
        save_all=True,
        append_images=img_list[1:],
        duration=2000,
        loop=0
    )
    print(f"✅ 폴라로이드 찰나 무비 생성 완료: {output_path}")
    return output_path

def process_queue():
    print("🚀 AI Pola 찰나 초경량 다이어트 공장 가동 시작! 주문을 기다립니다...")
    while True:
        try:
            # SQS 큐 대기열에서 주문서 1개 수령
            response = sqs.receive_message(QueueUrl=SQS_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20)
            
            if 'Messages' in response:
                for message in response['Messages']:
                    receipt_handle = message['ReceiptHandle']
                    body = message['Body']
                    local_image_paths = []
                    
                    try:
                        # 주문서 압축 해제 및 기입 데이터 분석
                        order_data = json.loads(body)
                        request_id = order_data.get("request_id", str(uuid.uuid4()))
                        s3_image_keys = order_data.get('s3_keys', [])
                        # app.py가 보낸 meta 정보 완벽 수령
                        meta = order_data.get('meta', {'date': '', 'place': '', 'message': ''})
                    except Exception as parse_err:
                        print(f"❌ 주문서 오염 및 파싱 실패: {parse_err}")
                        sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=receipt_handle)
                        continue

                    print(f"📦 주문 접수 완료! 번호: {request_id}, 인화할 사진: {len(s3_image_keys)}장")
                    local_gif_path = f"render_{request_id}.gif"
                    s3_gif_key = f"rendered/{request_id}.gif"

                    try:
                        # [공장 가동 1] S3 창고에서 유저가 올린 사진들 전량 다운로드
                        for i, s3_key in enumerate(s3_image_keys):
                            local_img_path = f"temp_{request_id}_{i}.jpg"
                            s3.download_file(S3_BUCKET, s3_key, local_img_path)
                            local_image_paths.append(local_img_path)
                        
                        # [공장 가동 2] 초경량 + 정밀 인화 렌더링 엔진 가동
                        make_light_gif(local_image_paths, local_gif_path, meta)
                        
                        # [공장 가동 3] 완성본 S3 창고로 업로드 배달
                        s3.upload_file(local_gif_path, S3_BUCKET, s3_gif_key)
                        print(f"☁️ S3 창고 배달 완료!: {s3_gif_key}")
                        
                    except Exception as inner_e:
                        print(f"⚠️ 개별 인화 공정 중 실패: {inner_e}")
                    finally:
                        # [공장 청소] 주문서 파기 및 내 컴퓨터 임시 쓰레기 파일 삭제
                        sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=receipt_handle)
                        for img_path in local_image_paths:
                            if os.path.exists(img_path): os.remove(img_path)
                        if os.path.exists(local_gif_path): os.remove(local_gif_path)
            else:
                pass
        except Exception as e:
            print(f"🚨 시스템 코어 에러: {e}")
            time.sleep(5)

if __name__ == "__main__":
    process_queue()