FROM python:3.11-slim

WORKDIR /app

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# requirements 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# outputs 폴더 생성
RUN mkdir -p /app/outputs

# 포트 노출
EXPOSE 8000

# FastAPI 서버 실행 (server.py 사용)
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
