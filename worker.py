import os
import time
import json
import uuid
import boto3
from PIL import Image, ImageOps
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")
AWS_REGION = "ap-northeast-2"

s3 = boto3.client('s3', region_name=AWS_REGION)
sqs = boto3.client('sqs', region_name=AWS_REGION)

def make_light_gif(image_paths, output_path):
    print(f"🎬 비율 유지 & 초경량 GIF 생성 시작: {image_paths}")
    
    img_list = []
    for path in image_paths:
        img = Image.open(path)
        # 💡 [핵심 다이어트] 스마트폰 고화질 4K 사진을 서버가 1초 만에 소화할 수 있게 즉시 축소 (비율 유지)
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        img_list.append(img)
    
    # 축소된 첫 번째 이미지의 크기를 기준 캔버스로 설정
    target_size = img_list[0].size
    
    resized_images = []
    for img in img_list:
        # 비율을 유지하며 빈 공간을 검은색('black')으로 패딩 처리 (찌그러짐 방지)
        padded_img = ImageOps.pad(img, target_size, color='black')
        
        if padded_img.mode != 'RGB':
            padded_img = padded_img.convert('RGB')
        resized_images.append(padded_img)
    
    # 2초 단위 무한 반복 GIF 저장
    resized_images[0].save(
        output_path,
        save_all=True,
        append_images=resized_images[1:],
        duration=2000,
        loop=0
    )
    print(f"✅ GIF 생성 완료: {output_path}")
    return output_path

def process_queue():
    print("🚀 AI Pola 초경량 다이어트 공장 가동 시작!")
    while True:
        try:
            response = sqs.receive_message(QueueUrl=SQS_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20)
            if 'Messages' in response:
                for message in response['Messages']:
                    receipt_handle = message['ReceiptHandle']
                    body = message['Body']
                    local_image_paths = []
                    
                    try:
                        order_data = json.loads(body)
                        request_id = order_data.get("request_id", str(uuid.uuid4()))
                        s3_image_keys = order_data.get('s3_keys', [order_data.get('s3_key', body)])
                    except:
                        request_id = str(uuid.uuid4())
                        s3_image_keys = [body]

                    print(f"📦 주문 접수! 번호: {request_id}")
                    local_gif_path = f"render_{request_id}.gif"
                    s3_gif_key = f"rendered/{request_id}.gif"

                    try:
                        for i, s3_key in enumerate(s3_image_keys):
                            local_img_path = f"temp_{request_id}_{i}.jpg"
                            s3.download_file(S3_BUCKET, s3_key, local_img_path)
                            local_image_paths.append(local_img_path)
                        
                        make_light_gif(local_image_paths, local_gif_path)
                        s3.upload_file(local_gif_path, S3_BUCKET, s3_gif_key)
                        print(f"☁️ S3 업로드 완료!: {s3_gif_key}")
                    except Exception as inner_e:
                        print(f"⚠️ 실패: {inner_e}")
                    finally:
                        sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=receipt_handle)
                        for img_path in local_image_paths:
                            if os.path.exists(img_path): os.remove(img_path)
                        if os.path.exists(local_gif_path): os.remove(local_gif_path)
            else:
                pass
        except Exception as e:
            print(f"🚨 에러: {e}")
            time.sleep(5)

if __name__ == "__main__":
    process_queue()