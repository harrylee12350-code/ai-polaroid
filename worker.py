import os
import time
import json
import uuid
import boto3
from moviepy.editor import ImageClip
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")
AWS_REGION = "ap-northeast-2"

s3 = boto3.client('s3', region_name=AWS_REGION)
sqs = boto3.client('sqs', region_name=AWS_REGION)

def make_zoom_video(image_path, output_path):
    print(f"🎬 렌더링 시작: {image_path}")
    clip = ImageClip(image_path).set_duration(10)
    w, h = clip.size
    w = w if w % 2 == 0 else w - 1
    h = h if h % 2 == 0 else h - 1
    clip = clip.resize(newsize=(w, h))
    clip.write_videofile(output_path, fps=24, codec='libx264', audio=False, logger=None)
    print(f"✅ 렌더링 완료: {output_path}")
    return output_path

def process_queue():
    print("🚀 AI Pola 렌더링 공장 가동 시작! 주문을 기다립니다...")
    while True:
        try:
            response = sqs.receive_message(QueueUrl=SQS_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20)
            if 'Messages' in response:
                for message in response['Messages']:
                    receipt_handle = message['ReceiptHandle']
                    body = message['Body']
                    try:
                        order_data = json.loads(body)
                        request_id = order_data.get("request_id", str(uuid.uuid4()))
                        if 's3_keys' in order_data and isinstance(order_data['s3_keys'], list):
                            s3_image_key = order_data['s3_keys'][0]
                        else:
                            s3_image_key = order_data.get('s3_key', body)
                    except:
                        request_id = str(uuid.uuid4())
                        s3_image_key = body

                    print(f"📦 주문 접수! 주문번호: {request_id}")

                    local_image_path = f"temp_{request_id}.jpg"
                    local_video_path = f"render_{request_id}.mp4"
                    s3_video_key = f"rendered/{request_id}.mp4"

                    try:
                        s3.download_file(S3_BUCKET, s3_image_key, local_image_path)
                        make_zoom_video(local_image_path, local_video_path)
                        s3.upload_file(local_video_path, S3_BUCKET, s3_video_key)
                        print(f"☁️ S3 업로드 완료!: {s3_video_key}")
                    except Exception as inner_e:
                        print(f"⚠️ 렌더링/업로드 실패: {inner_e}")
                    finally:
                        sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=receipt_handle)
                        if os.path.exists(local_image_path): os.remove(local_image_path)
                        if os.path.exists(local_video_path): os.remove(local_video_path)
            else:
                pass
        except Exception as e:
            print(f"🚨 시스템 에러: {e}")
            time.sleep(5)

if __name__ == "__main__":
    process_queue()