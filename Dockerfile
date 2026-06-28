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

# 6. 앞문(웹사이트)과 뒷문(공장)을 동시에 여는 핵심 명령어!
CMD ["sh", "-c", "python worker.py & streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"]