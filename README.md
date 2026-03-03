# 찬호의 놀이터 🎪

**Text to Image 기능 추가!** 완전히 작동하는 AI 이미지 생성

![Bootstrap 5](https://img.shields.io/badge/Bootstrap-5.3-purple)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)

## ✨ 주요 기능

### 🎨 Text to Image (NEW!) ⭐⭐

**완전 구현! 지금 바로 사용 가능!**

- ✅ Replicate (Stable Diffusion XL)
- ✅ Stability AI
- ✅ OpenAI DALL-E 3
- ✅ 프롬프트 자동 개선
- ✅ 다중 이미지 생성 (최대 4개)
- ✅ 크기 조절 (256-2048px)

### 🎬 Story to Music Video

- ✅ NLP 분석 완료
- 🟡 Music/Video (API 연동만)

## 🚀 빠른 시작

```bash
# Docker
docker-compose up -d

# 또는 로컬
cd backend && python main.py
cd frontend && python -m http.server 8080
```

접속: http://localhost:8080

## 🎨 Text to Image 사용

### 웹 UI:
1. "Text to Image" 섹션으로 이동
2. 프롬프트 입력: "숲 속의 마법 나무, 판타지 스타일"
3. 크기/개수 선택
4. 생성 클릭!

### API:
```bash
curl -X POST "http://localhost:8000/api/text-to-image/generate" \
  -F "prompt=a cute cat" \
  -F "width=512" \
  -F "height=512"
```

## 🔑 API 키 설정

### Replicate (추천)
```bash
export REPLICATE_API_TOKEN="r8_xxxxx"
```

https://replicate.com 에서 무료 크레딧 받기

### 또는 Stability AI / DALL-E
```bash
export STABILITY_API_KEY="sk-xxxxx"
export OPENAI_API_KEY="sk-xxxxx"
```

## 📂 구조

```
├── frontend/
│   ├── index.html      # Text to Image 폼
│   └── js/script.js    # API 연동
├── backend/
│   └── app/
│       ├── routers/
│       │   └── text_to_image.py  # ⭐ NEW
│       └── services/
│           └── image.py          # ⭐ 이미지 생성
```

## 💡 프롬프트 팁

```
좋은 예시:
"a magical glowing tree in enchanted forest, fantasy style, 
dramatic lighting, highly detailed, 8k"

네거티브:
"blurry, low quality, distorted"
```

## 📦 설치

### API 키 있을 때:
```bash
pip install replicate requests pillow
export REPLICATE_API_TOKEN="r8_xxxxx"
python main.py
```

### API 키 없을 때 (테스트):
```bash
pip install fastapi uvicorn
python main.py
# 임시 경로 반환
```

## 📊 기능 상태

| 기능 | 상태 |
|------|------|
| Text to Image | ✅ 완료 |
| Story to MV (NLP) | ✅ 완료 |
| Music 생성 | 🟡 구조 완성 |
| Video 생성 | 🟡 구조 완성 |

## 🏠 NAS 배포

Container Manager → 환경 변수 추가:
- `REPLICATE_API_TOKEN`
- `STABILITY_API_KEY`
- `OPENAI_API_KEY`

---

Made with ❤️ by Chanho
