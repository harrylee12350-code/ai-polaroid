import os, time, json, uuid, boto3
from PIL import Image, ImageOps, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()
S3_BUCKET = "aipola-temp-storage-1782548118"
SQS_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/737138011566/aipola-render-queue")
s3, sqs = boto3.client('s3', region_name='ap-northeast-2'), boto3.client('sqs', region_name='ap-northeast-2')

def make_light_gif(image_paths, output_path, meta):
    img_list = []
    # 폰트 에러 방지 (기본 폰트 사용)
    font = ImageFont.load_default()
    
    for path in image_paths:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # 캔버스 확장 및 텍스트 입히기
        w, h = img.size
        canvas = Image.new("RGB", (w, h + 120), "white")
        canvas.paste(img, (0, 0))
        draw = ImageDraw.Draw(canvas)
        text = f"{meta.get('date', '')} | {meta.get('place', '')}\n{meta.get('message', '')}"
        draw.text((20, h + 20), text, fill="black", font=font)
        img_list.append(canvas)
    
    img_list[0].save(output_path, save_all=True, append_images=img_list[1:], duration=2000, loop=0)
    return output_path

def process_queue():
    while True:
        resp = sqs.receive_message(QueueUrl=SQS_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20)
        if 'Messages' in resp:
            for msg in resp['Messages']:
                data = json.loads(msg['Body'])
                req_id = data['request_id']
                # 💡 주문서에서 meta 정보 확인
                meta = data.get('meta', {'date': '', 'place': '', 'message': ''})
                
                # 이미지 다운로드 및 GIF 제작 로직 수행
                # ... (이전 코드 로직 동일) ...
                
                sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=msg['ReceiptHandle'])
        time.sleep(1)