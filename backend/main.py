from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.routers import text_to_image, two_d_to_three_d, story_to_mv, local_llm, youtube

app = FastAPI(
    title="찬호의 놀이터 API",
    description="AI 기반 창작 도구 API",
    version="1.0.0"
)

# outputs 폴더를 /files 경로로 서빙
outputs_dir = Path("./outputs")
outputs_dir.mkdir(exist_ok=True)

# 하위 디렉토리 생성
(outputs_dir / "samples").mkdir(exist_ok=True)
(outputs_dir / "clips").mkdir(exist_ok=True)
(outputs_dir / "final").mkdir(exist_ok=True)

# sessions 폴더 생성
sessions_dir = Path("./sessions")
sessions_dir.mkdir(exist_ok=True)

app.mount("/files", StaticFiles(directory=outputs_dir), name="files")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # 개발 환경
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(text_to_image.router, prefix="/api/text-to-image", tags=["Text to Image"])
app.include_router(two_d_to_three_d.router, prefix="/api/2d-to-3d", tags=["2D to 3D"])
app.include_router(story_to_mv.router, prefix="/api/story-to-mv", tags=["Story to MV"])
app.include_router(local_llm.router, prefix="/api/local-llm", tags=["Local LLM"])
app.include_router(youtube.router, prefix="/api/youtube", tags=["YouTube"])


@app.get("/")
async def root():
    return {
        "message": "찬호의 놀이터 API에 오신 것을 환영합니다!",
        "docs": "/docs",
        "version": "1.1.0",
        "endpoints": {
            "story_to_mv": "/api/story-to-mv/generate",
            "mv_wizard": "/api/story-to-mv/session/create",
            "text_to_image": "/api/text-to-image/generate",
            "2d_to_3d": "/api/2d-to-3d/convert",
            "local_llm": "/api/local-llm/chat",
            "youtube": "/api/youtube/status"
        }
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
