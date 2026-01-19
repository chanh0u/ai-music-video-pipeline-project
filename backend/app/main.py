from fastapi import FastAPI, Form

from .schemas import GenerateResponse
from .services import nlp, music, video
from .storage import upload_s3
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Story Music MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/generate", response_model=GenerateResponse)
async def generate(
    story: str = Form(...),
    genre: str = Form("ballad"),
    voice: str = Form("female")
):
    # 1. 요약 + 감정 분석
    summary, emotion = nlp.analyze_story(story)

    # 2. 가사 생성
    lyrics = nlp.generate_lyrics(summary, emotion)

    # 3. 음악 생성 (30초)
    audio_path = music.generate_music(lyrics, genre, voice)

    # 4. 이미지 기반 영상 생성
    video_path = video.generate_video(summary, audio_path)

    # 5. 업로드
    audio_url = upload_s3(audio_path)
    video_url = upload_s3(video_path)

    return GenerateResponse(
        audio_url=audio_url,
        video_url=video_url,
        emotion=emotion
    )