import boto3
import json
import os
import subprocess
from botocore.exceptions import ClientError

# 설정 (Secrets에서 불러오거나 config.json 활용)
QUEUE_URL = "여기에_SQS_큐_URL_입력"
BUCKET_NAME = "aipola-temp-storage-1782548118"
s3 = boto3.client('s3')
sqs = boto3.client('sqs')

def process_video(request_id, s3_keys):
    # 1. 사진 다운로드
    local_dir = f"temp_{request_id}"
    os.makedirs(local_dir, exist_ok=True)
    
    for i, key in enumerate(s3_keys):
        s3.download_file(BUCKET_NAME, key, f"{local_dir}/img_{i}.jpg")
    
    # 2. FFmpeg로 영상 합성 (10초 길이, 이미지당 2초)
    output_file = f"{request_id}_final.mp4"
    # 예시: 3장의 사진을 2초씩 보여주는 간단한 명령
    cmd = [
        'ffmpeg', '-loop', '1', '-t', '2', '-i', f"{local_dir}/img_0.jpg",
        '-loop', '1', '-t', '2', '-i', f"{local_dir}/img_1.jpg",
        '-loop', '1', '-t', '2', '-i', f"{local_dir}/img_2.jpg",
        '-filter_complex', '[0:v]fade=t=out:st=1.5:d=0.5[v0];[1:v]fade=t=in:st=0:d=0.5,fade=t=out:st=1.5:d=0.5[v1];[2:v]fade=t=in:st=0:d=0.5[v2];[v0][v1][v2]concat=n=3:v=1:a=0[v]',
        '-map', '[v]', '-pix_fmt', 'yuv420p', '-y', output_file
    ]
    subprocess.run(cmd)
    
    # 3. 결과물 S3 업로드
    s3.upload_file(output_file, BUCKET_NAME, f"results/{output_file}")
    print(f"영상 제작 완료: {output_file}")

# 4. 메인 루프: 대기열 감시
def main():
    print("영상 렌더링 엔진 가동 중...")
    while True:
        response = sqs.receive_message(QueueUrl=QUEUE_URL, WaitTimeSeconds=20)
        if 'Messages' in response:
            for msg in response['Messages']:
                data = json.loads(msg['Body'])
                process_video(data['request_id'], data['s3_keys'])
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg['ReceiptHandle'])

if __name__ == "__main__":
    main()