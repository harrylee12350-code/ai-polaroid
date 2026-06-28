import os
import time
import json
import uuid
import boto3
import urllib.request  # 💡 폰트 다운로드를 위한 모듈 추가
from PIL import Image, ImageOps, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")
AWS_REGION = "ap-northeast-2"

s3 = boto3.client('s3', region_name=AWS_REGION)
sqs = boto3.client('sqs', region_name=AWS_REGION)

# 💡 [핵심 해결책] Railway 서버에 한글 폰트(나눔고딕)를 강제로 다운로드하여 장착합니다!
def get_korean_font():
    font_path = "NanumGothic.ttf"
    if not os.path.exists(font_path):
        print("⬇️ 한글 폰트 자동 다운로드 중...")
        url = "https://github.com/naver/nanumfont/raw/master/NanumFont_TTF_ALL/NanumGothic.ttf"
        try:
            urllib.request.urlretrieve(url, font_path)
        except Exception as e:
            print(f"⚠️ 폰트 다운로드 실패: {e}")
            return ImageFont.load_default()
    
    try:
        return ImageFont.truetype(font_path, 24)
    except:
        return ImageFont.load_default()

def make_light_gif(image_paths, output_path, meta):
    print(f"🎬 비율 유지 & 텍스트 정밀 인화 시작: {meta}")
    
    raw_imgs = []
    for path in image_paths:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        raw_imgs.append(img)
    
    target_w, target_h = raw_imgs[0].size
    font = get_korean_font()  # 한글 폰트 불러오기
    
    img_list = []
    for img in raw_imgs:
        padded_img = ImageOps.pad(img, (target_w, target_h), color='white')
        canvas = Image.new("RGB", (target_w, target_h + 140), "white")
        canvas.paste(padded_img, (0, 0))
        
        draw = ImageDraw.Draw(canvas)
        date_str = meta.get('date', '')
        place_str = meta.get('place', '')
        msg_str = meta.get('message', '')
        
        # 에러를 유발하는 이모지를 빼고, 깔끔하고 감성적인 폴라로이드 스타일로 변경
        text_line1 = f"[{date_str}]  {place_str}"
        text_line2 = f"\" {msg_str} \""
        
        # 텍스트 색상을 진한 회색으로 하여 감성 극대화
        draw.text((30, target_h + 30), text_line1, fill="#555555", font=font)
        draw.text((30, target_h + 80), text_line2, fill="#111111", font=font)
        
        img_list.append(canvas)
    
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
            response = sqs.receive_message(QueueUrl=SQS_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20)
            
            if 'Messages' in response:
                for message in response['Messages']:
                    receipt_handle = message['ReceiptHandle']
                    body = message['Body']
                    local_image_paths = []
                    
                    try:
                        order_data = json.loads(body)
                        request_id = order_data.get("request_id", str(uuid.uuid4()))
                        s3_image_keys = order_data.get('s3_keys', [])
                        meta = order_data.get('meta', {'date': '', 'place': '', 'message': ''})
                    except Exception as parse_err:
                        print(f"❌ 주문서 파싱 실패: {parse_err}")
                        sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=receipt_handle)
                        continue

                    print(f"📦 주문 접수 완료! 번호: {request_id}")
                    local_gif_path = f"render_{request_id}.gif"
                    s3_gif_key = f"rendered/{request_id}.gif"

                    try:
                        for i, s3_key in enumerate(s3_image_keys):
                            local_img_path = f"temp_{request_id}_{i}.jpg"
                            s3.download_file(S3_BUCKET, s3_key, local_img_path)
                            local_image_paths.append(local_img_path)
                        
                        make_light_gif(local_image_paths, local_gif_path, meta)
                        s3.upload_file(local_gif_path, S3_BUCKET, s3_gif_key)
                        print(f"☁️ S3 창고 배달 완료!: {s3_gif_key}")
                        
                    except Exception as inner_e:
                        print(f"⚠️ 렌더링 실패: {inner_e}")
                    finally:
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