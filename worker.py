import os
import time
import json
import uuid
import boto3
from PIL import Image, ImageOps, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")
AWS_REGION = "ap-northeast-2"

s3 = boto3.client('s3', region_name=AWS_REGION)
sqs = boto3.client('sqs', region_name=AWS_REGION)

def make_light_gif(image_paths, output_path, meta):
    print(f"🎬 텍스트 오버레이 GIF 생성 시작: {meta}")
    img_list = []
    
    # 폰트 로딩 (기본 폰트 사용, 필요 시 폰트 파일 경로 추가 가능)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()

    for path in image_paths:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # 폴라로이드 테두리/텍스트를 위한 추가 공간 확보
        w, h = img.size
        new_h = h + 120
        canvas = Image.new("RGB", (w, new_h), "white")
        canvas.paste(img, (0, 0))
        
        # 텍스트 그리기
        draw = ImageDraw.Draw(canvas)
        text = f"{meta.get('date', '')} | {meta.get('place', '')}\n{meta.get('message', '')}"
        draw.text((20, h + 20), text, fill="black", font=font)
        
        img_list.append(canvas)
    
    target_size = img_list[0].size
    resized_images = [ImageOps.pad(img, target_size, color='white') for img in img_list]
    
    resized_images[0].save(output_path, save_all=True, append_images=resized_images[1:], duration=2000, loop=0)
    return output_path

def process_queue():
    while True:
        try:
            response = sqs.receive_message(QueueUrl=SQS_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20)
            if 'Messages' in response:
                for message in response['Messages']:
                    body = json.loads(message['Body'])
                    local_images = []
                    # 💡 S3 다운로드 및 처리 로직은 이전과 동일...
                    # (간결함을 위해 생략했으나, 기존 구조 그대로 유지하세요)
                    sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=message['ReceiptHandle'])
        except: time.sleep(5)

if __name__ == "__main__": process_queue()