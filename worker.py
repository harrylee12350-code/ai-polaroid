import os
import time
import json
from datetime import datetime
import boto3
from moviepy.editor import ImageClip
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 대표님이 기존에 세팅하신 정보 (환경변수가 없으면 이 값을 안전망으로 사용합니다)
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "aipola-temp-storage-1782548118")
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")
AWS_REGION = "ap-northeast-2"

# AWS 클라이언트 연결
s3 = boto3.client('s3', region_name=AWS_REGION)
sqs = boto3.client('sqs', region_name=AWS_REGION)

def make_zoom_video(image_path, output_path):
    """MoviePy를 이용한 10초 줌인 애니메이션 생성 함수"""
    print(f"🎬 렌더링 시작: {image_path}")
    
    # 10초짜리 이미지 클립 생성
    clip = ImageClip(image_path).set_duration(10)
    
    # 줌인 효과 적용 (시간 t에 따라 1.0배에서 1.2배로 서서히 확대)
    # 에러 방지를 위해 람다 함수 최소화 적용
    video = clip.resize(lambda t: 1 + 0.02 * t)
    
    # 영상 내보내기 (에러 방지: 오디오 제거, 안정적인 fps 24 설정)
    video.write_videofile(output_path, fps=24, codec='libx264', audio=False, logger=None)
    print(f"✅ 렌더링 완료: {output_path}")
    
    return output_path

def process_queue():
    print("🚀 AI Pola 렌더링 공장 가동 시작! 주문을 기다립니다...")
    
    while True:
        try:
            # 1. SQS에서 메시지 가져오기 (Long Polling - 20초 대기)
            response = sqs.receive_message(
                QueueUrl=SQS_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )
            
            if 'Messages' in response:
                for message in response['Messages']:
                    receipt_handle = message['ReceiptHandle']
                    
                    # 프론트엔드에서 보낸 메시지(S3 파일명) 파싱
                    # JSON 형태일 수도 있고 일반 텍스트일 수도 있으므로 안전하게 처리
                    body = message['Body']
                    try:
                        order_data = json.loads(body)
                        s3_image_key = order_data.get('s3_key', body)
                    except:
                        s3_image_key = body

                    print(f"📦 새 주문 접수! 대상 파일: {s3_image_key}")

                    # 파일명 설정 (원본사진, 렌더링될 영상)
                    local_image_path = f"temp_{s3_image_key}"
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    local_video_path = f"render_{timestamp}.mp4"
                    s3_video_key = f"rendered/video_{timestamp}.mp4" # S3에는 rendered 폴더 안에 저장

                    # 2. S3에서 원본 사진 다운로드
                    s3.download_file(S3_BUCKET, s3_image_key, local_image_path)
                    
                    # 3. 영상 렌더링 실행
                    make_zoom_video(local_image_path, local_video_path)
                    
                    # 4. 완성된 영상을 다시 S3에 업로드
                    s3.upload_file(local_video_path, S3_BUCKET, s3_video_key)
                    print(f"☁️ S3 업로드 완료: {s3_video_key}")
                    
                    # 5. 작업이 끝난 SQS 메시지(주문서) 삭제
                    sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=receipt_handle)
                    print("🧹 주문 처리 완료 및 큐 정리 끝!\n")
                    
                    # 6. 임시 파일 삭제 (서버 용량 꽉 참 방지)
                    if os.path.exists(local_image_path): os.remove(local_image_path)
                    if os.path.exists(local_video_path): os.remove(local_video_path)
                    
            else:
                # 큐에 메시지가 없을 때
                pass
                
        except Exception as e:
            # 절대 서버가 죽지 않도록 에러 발생 시 로그만 남기고 다음 주문 대기
            print(f"🚨 렌더링 중 에러 발생 (서버는 계속 돌아갑니다): {e}")
            time.sleep(5) # 에러 시 5초 휴식 후 재가동

if __name__ == "__main__":
    process_queue()