# 1. 파이썬 환경 가져오기 (가벼운 버전)
FROM python:3.10-slim

# 2. 핵심! 영상 처리에 필수적인 FFmpeg 설치 (이게 없으면 에러 발생)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. 작업할 폴더 지정
WORKDIR /app

# 4. 필요한 파이썬 라이브러리 목록 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 우리의 핵심 코드(worker.py 등) 복사
COPY . .

# 6. 서버가 켜질 때 실행할 명령어 (렌더링 워커 가동)
CMD ["python", "worker.py"]