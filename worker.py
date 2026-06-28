import os
import time
import json
import uuid
import boto3
from moviepy.editor import ImageClip, concatenate_videoclips
from dotenv import load_dotenv

load_dotenv()

# S3 창고 및 SQS 큐 고정 주소
S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")
AWS_REGION = "ap-northeast-2"

s3 = boto3.client('s3', region_name=AWS_REGION)
sqs = boto3.client('sqs', region_name=AWS_REGION)

def make_slideshow_video(image_paths, output_path):
    print(f"🎬 렌더링 시작: {image_paths}")
    clips = []
    total_duration = 10.0
    duration_per_image = total_duration / len(image_paths)
    
    # 첫 번째 이미지 기준으로 기준 해상도 세팅 (짝수 고정으로 재생 오류 방지)
    temp_clip = ImageClip(image_paths[0])
    w, h = temp_clip.size
    w = w if w % 2 == 0 else w - 1
    h = h if h % 2 == 0 else h - 1
    temp_clip.close()
    
    # 💡 [핵심 수정] 업로드된 모든 사진을 순서대로 규격에 맞춰 클립화
    for path in image_paths:
        clip = ImageClip(path).set_duration(duration_per_image)
        clip = clip.resize(newsize=(w, h))
        clips.append(clip)
        
    # 사진들을 하나의 이어지는 비디오로 결합
    final_clip = concatenate_videoclips(clips, method="compose")
    
    # 💡 [속도 극대화] 모바일 10초 이내 응답을 위해 인코딩 부하를 제로에 가깝게 세팅
    final_clip.write_videofile(output_path, fps=15, codec='libx264', preset='ultrafast', audio=False, logger=None)
    
    final_clip.close()
    for c in clips:
        c.close()
        
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
                    local_image_paths = []
                    local_video_path = ""
                    
                    try:
                        order_data = json.loads(body)
                        request_id = order_data.get("request_id", str(uuid.uuid4()))
                        if 's3_keys' in order_data and isinstance(order_data['s3_keys'], list):
                            s3_image_keys = order_data['s3_keys']
                        else:
                            s3_image_keys = [order_data.get('s3_key', body)]
                    except:
                        request_id = str(uuid.uuid4())
                        s3_image_keys = [body]

                    print(f"📦 주문 접수! 주문번호: {request_id}, 사진 개수: {len(s3_image_keys)}")

                    local_video_path = f"render_{request_id}.mp4"
                    s3_video_key = f"rendered/{request_id}.mp4"

                    try:
                        # 💡 [핵심 수정] 리스트에 들어있는 모든 사진 S3에서 한 번에 다운로드
                        for i, s3_key in enumerate(s3_image_keys):
                            local_img_path = f"temp_{request_id}_{i}.jpg"
                            s3.download_file(S3_BUCKET, s3_key, local_img_path)
                            local_image_paths.append(local_img_path)
                        
                        # 슬라이드쇼 비디오 제작 실행
                        make_slideshow_video(local_image_paths, local_video_path)
                        
                        s3.upload_file(local_video_path, S3_BUCKET, s3_video_key)
                        print(f"☁️ S3 업로드 완료!: {s3_video_key}")
                    except Exception as inner_e:
                        print(f"⚠️ 렌더링/업로드 실패: {inner_e}")
                    finally:
                        sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=receipt_handle)
                        for img_path in local_image_paths:
                            if os.path.exists(img_path): os.remove(img_path)
                        if local_video_path and os.path.exists(local_video_path): os.remove(local_video_path)
            else:
                pass
        except Exception as e:
            print(f"🚨 시스템 에러: {e}")
            time.sleep(5)

if __name__ == "__main__":
    process_queue()