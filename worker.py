import os
import time
import json
from datetime import datetime
import boto3
from moviepy.editor import ImageClip
from dotenv import load_dotenv

load_dotenv()

# S3 창고 대못 박기 유지!
S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")
AWS_REGION = "ap-northeast-2"

s3 = boto3.client('s3', region_name=AWS_REGION)
sqs = boto3.client('sqs', region_name=AWS_REGION)

def make_zoom_video(image_path, output_path):
    print(f"🎬 렌더링 시작: {image_path}")
    
    # 1. 이미지를 불러와서 10초짜리 클립으로 만듭니다.
    clip = ImageClip(image_path).set_duration(10)
    
    # 2. (핵심) H.264 코덱은 가로세로 픽셀이 '짝수'여야 블랙 스크린이 안 뜹니다. 짝수로 강제 조정!
    w, h = clip.size
    w = w if w % 2 == 0 else w - 1
    h = h if h % 2 == 0 else h - 1
    clip = clip.resize(newsize=(w, h))
    
    # 3. 줌인 효과를 빼고 가장 안전하게 정적 영상으로 렌더링합니다.
    clip.write_videofile(output_path, fps=24, codec='libx264', audio=False, logger=None)
    print(f"✅ 렌더링 완료: {output_path}")
    return output_path

def process_queue():
    print("🚀 AI Pola 렌더링 공장 가동 시작! 주문을 기다립니다...")
    
    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )
            
            if 'Messages' in response:
                for message in response['Messages']:
                    receipt_handle = message['ReceiptHandle']
                    body = message['Body']
                    
                    try:
                        order_data = json.loads(body)
                        if 's3_keys' in order_data and isinstance(order_data['s3_keys'], list):
                            s3_image_key = order_data['s3_keys'][0]
                        else:
                            s3_image_key = order_data.get('s3_key', body)
                    except:
                        s3_image_key = body

                    print(f"📦 새 주문 접수! 타겟 파일: {s3_image_key}")

                    local_image_path = f"temp_image.jpg"
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    local_video_path = f"render_{timestamp}.mp4"
                    s3_video_key = f"rendered/video_{timestamp}.mp4"

                    try:
                        s3.download_file(S3_BUCKET, s3_image_key, local_image_path)
                        make_zoom_video(local_image_path, local_video_path)
                        s3.upload_file(local_video_path, S3_BUCKET, s3_video_key)
                        print(f"☁️ S3 업로드 완료! 영화가 서버에 저장되었습니다: {s3_video_key}")
                    except Exception as inner_e:
                        print(f"⚠️ 개별 주문 처리 실패: {inner_e}")
                    finally:
                        sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=receipt_handle)
                        print("🧹 주문서 파기 및 큐 정리 완료!\n")
                        
                        if os.path.exists(local_image_path): os.remove(local_image_path)
                        if os.path.exists(local_video_path): os.remove(local_video_path)
            else:
                pass
                
        except Exception as e:
            print(f"🚨 시스템 에러 발생 (서버는 계속 돌아갑니다): {e}")
            time.sleep(5)

if __name__ == "__main__":
    process_queue()