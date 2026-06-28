# 1. 파이썬 환경 (로그 즉각 출력을 위한 무버퍼링 설정 추가!)
FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1

# 2. 영상 처리용 FFmpeg 설치
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. 작업 폴더 설정
WORKDIR /app

# 4. 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 코드 복사
COPY . .

# 6. 실행 (이메일 묻기 방지 headless 설정 추가 & 동시 실행)
CMD sh -c "python worker.py & streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true"