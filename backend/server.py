# server.py
"""
찬호의 놀이터 API - 통합 서버
AI 기반 창작 도구 API (Text-to-Image, 2D-to-3D, Story-to-MV)
"""
from fastapi import FastAPI, APIRouter, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import uuid
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Fix Windows console encoding for Korean
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Debug: Print loaded API keys status
print("\n[CONFIG] API Keys Status:")
print(f"  - REPLICATE_API_TOKEN: {'Set' if os.getenv('REPLICATE_API_TOKEN') else 'Not set'}")
print(f"  - STABILITY_API_KEY: {'Set' if os.getenv('STABILITY_API_KEY') else 'Not set'}")
print(f"  - OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
print(f"  - ANTHROPIC_API_KEY: {'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not set'}")
print()


# ============================================================
# Pydantic Schemas
# ============================================================

class TextToImageResponse(BaseModel):
    """이미지 생성 응답"""
    status: str
    prompt: str
    enhanced_prompt: Optional[str] = None
    image_urls: List[str]
    count: int


class GenerateResponse(BaseModel):
    """Story to MV 생성 응답"""
    audio_url: str
    video_url: str
    emotion: str
    summary: Optional[str] = None
    lyrics: Optional[str] = None


# ============================================================
# Storage Service
# ============================================================

def get_local_url(file_path, base_url: str = "http://localhost:8000"):
    """로컬 파일 경로를 서빙 가능한 URL로 변환"""
    if not file_path:
        return None
    path = Path(file_path)
    filename = path.name
    return f"{base_url}/files/{filename}"


def upload_s3(file_path):
    """
    개발 환경: 로컬 URL 반환
    프로덕션: S3 업로드 (주석 해제 필요)
    """
    if not file_path:
        return None
    # 프로덕션용 S3 업로드
    # import boto3
    # s3 = boto3.client("s3")
    # BUCKET = "chanho-playground"
    # key = f"outputs/{uuid.uuid4()}/{Path(file_path).name}"
    # s3.upload_file(file_path, BUCKET, key)
    # return f"https://{BUCKET}.s3.amazonaws.com/{key}"

    # 개발용: 로컬 URL 반환
    return get_local_url(file_path)


# ============================================================
# Image Service
# ============================================================

def generate_image_replicate(
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    num_outputs: int = 1
):
    """Replicate API로 이미지 생성 (Stable Diffusion)"""
    try:
        import replicate
        import requests

        print(f"[IMAGE] Generating image with Replicate...")
        print(f"  - Prompt: {prompt}")
        print(f"  - Size: {width}x{height}")

        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_outputs": num_outputs,
                "scheduler": "K_EULER",
                "num_inference_steps": 50,
                "guidance_scale": 7.5,
            }
        )

        image_paths = []
        for i, image_url in enumerate(output):
            print(f"  - Downloading: {i+1}/{len(output)}")
            response = requests.get(image_url)
            output_path = f"./outputs/image_{uuid.uuid4()}.png"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(response.content)
            image_paths.append(output_path)
            print(f"  > Saved: {output_path}")

        return image_paths

    except ImportError:
        print("[ERROR] replicate package is not installed.")
        raise
    except Exception as e:
        print(f"[ERROR] Replicate image generation failed: {str(e)}")
        raise


def generate_image_stability(
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    style_preset: str = None
):
    """Stability AI 공식 API로 이미지 생성"""
    try:
        import requests
        import base64

        api_key = os.getenv("STABILITY_API_KEY")
        if not api_key:
            raise ValueError("STABILITY_API_KEY 환경 변수가 설정되지 않았습니다.")

        print(f"[IMAGE] Generating image with Stability AI...")
        print(f"  - Prompt: {prompt}")
        print(f"  - Size: {width}x{height}")

        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "text_prompts": [
                    {"text": prompt, "weight": 1},
                    {"text": negative_prompt, "weight": -1}
                ] if negative_prompt else [{"text": prompt}],
                "cfg_scale": 7,
                "height": height,
                "width": width,
                "samples": 1,
                "steps": 30,
            }
        )

        if response.status_code != 200:
            raise Exception(f"API 오류: {response.text}")

        data = response.json()
        output_path = f"./outputs/image_{uuid.uuid4()}.png"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(base64.b64decode(data["artifacts"][0]["base64"]))

        print(f"  > Saved: {output_path}")
        return [output_path]

    except Exception as e:
        print(f"[ERROR] Stability AI image generation failed: {str(e)}")
        raise


def generate_image_dalle(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    n: int = 1
):
    """OpenAI DALL-E로 이미지 생성"""
    try:
        from openai import OpenAI
        import requests

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        client = OpenAI(api_key=api_key)
        print(f"[IMAGE] Generating image with DALL-E...")

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
        )

        image_paths = []
        for i, image_data in enumerate(response.data):
            print(f"  - Downloading: {i+1}/{len(response.data)}")
            image_response = requests.get(image_data.url)
            output_path = f"./outputs/image_{uuid.uuid4()}.png"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_response.content)
            image_paths.append(output_path)
            print(f"  > Saved: {output_path}")

        return image_paths

    except Exception as e:
        print(f"[ERROR] DALL-E image generation failed: {str(e)}")
        raise


def generate_image(
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    num_outputs: int = 1,
    provider: str = "replicate"
):
    """이미지 생성 (여러 제공자 지원)"""
    if os.getenv("REPLICATE_API_TOKEN") is None and provider == "replicate":
        print("[WARNING] REPLICATE_API_TOKEN is not set.")
        print("[IMAGE] Generating test image...")
        print(f"  - Prompt: {prompt}")
        print(f"  - Size: {width}x{height}")
        print(f"  - Count: {num_outputs}")

        # 테스트용: picsum.photos에서 랜덤 이미지 다운로드
        import requests
        image_paths = []
        for i in range(num_outputs):
            output_path = f"./outputs/image_{uuid.uuid4()}.png"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            try:
                response = requests.get(f"https://picsum.photos/{width}/{height}", timeout=10)
                with open(output_path, "wb") as f:
                    f.write(response.content)
                image_paths.append(output_path)
                print(f"  > Test image saved: {output_path}")
            except Exception as e:
                print(f"  [ERROR] Failed to download test image: {e}")
                image_paths.append(output_path)
        return image_paths

    if provider == "replicate":
        return generate_image_replicate(prompt, negative_prompt, width, height, num_outputs)
    elif provider == "stability":
        # Stability AI SDXL only supports specific sizes
        sdxl_sizes = [(1024, 1024), (1152, 896), (1216, 832), (1344, 768), (1536, 640),
                      (640, 1536), (768, 1344), (832, 1216), (896, 1152)]
        # Find closest supported size
        if (width, height) not in sdxl_sizes:
            width, height = 1024, 1024
            print(f"  [INFO] Adjusted size to {width}x{height} for Stability AI")
        return generate_image_stability(prompt, negative_prompt, width, height)
    elif provider == "dalle":
        # DALL-E 3 only supports: 1024x1024, 1024x1792, 1792x1024
        dalle_sizes = {"square": "1024x1024", "portrait": "1024x1792", "landscape": "1792x1024"}
        if width == height:
            size = "1024x1024"
        elif height > width:
            size = "1024x1792"
        else:
            size = "1792x1024"
        print(f"  [INFO] Adjusted size to {size} for DALL-E 3")
        return generate_image_dalle(prompt, size, n=num_outputs)
    else:
        raise ValueError(f"지원하지 않는 제공자: {provider}")


def enhance_prompt(prompt: str):
    """프롬프트 개선"""
    if prompt and not any(word in prompt.lower() for word in ["detailed", "high quality", "masterpiece"]):
        return f"{prompt}, highly detailed, masterpiece, best quality, 8k"
    return prompt


# ============================================================
# NLP Service
# ============================================================

def summarize_and_emotion(story: str):
    """스토리 요약 및 감정 분석"""
    summary = story[:100] + "..." if len(story) > 100 else story

    emotion = "neutral"
    if any(word in story.lower() for word in ["행복", "기쁨", "웃음", "happy", "joy"]):
        emotion = "happy"
    elif any(word in story.lower() for word in ["슬픔", "눈물", "sad", "cry"]):
        emotion = "sad"
    elif any(word in story.lower() for word in ["화", "분노", "angry", "mad"]):
        emotion = "angry"
    elif any(word in story.lower() for word in ["사랑", "love", "romance"]):
        emotion = "romantic"

    return summary, emotion


def generate_lyrics(summary: str, emotion: str):
    """요약과 감정을 바탕으로 가사 생성"""
    emotion_templates = {
        "happy": "밝은 햇살 아래\n우리의 이야기가 시작돼\n행복한 순간들\n영원히 기억할게",
        "sad": "눈물이 흐르는 밤\n그리운 기억들\n슬픈 멜로디에\n마음을 담아",
        "angry": "불타는 감정\n억눌린 외침\n이제는 말할게\n내 진심을",
        "romantic": "사랑하는 마음\n너에게 전하고 싶어\n영원한 약속\n함께 하자고",
        "neutral": "우리의 이야기\n담담하게 흘러가\n평온한 일상 속\n특별한 순간들"
    }

    lyrics = emotion_templates.get(emotion, emotion_templates["neutral"])
    return f"[Verse 1]\n{summary[:50]}...\n\n[Chorus]\n{lyrics}\n\n[Verse 2]\n계속되는 우리의 여정\n함께 만들어가는 이야기"


# ============================================================
# Music Service
# ============================================================

def generate_music(duration: int, genre: str, voice: str, lyrics: str):
    """AI로 음악 생성"""
    import requests

    output_path = f"./outputs/music_{uuid.uuid4()}.mp3"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"[MUSIC] Music generation request:")
    print(f"  - Duration: {duration}s")
    print(f"  - Genre: {genre}")
    print(f"  - Voice: {voice}")

    # 테스트용: 샘플 음악 다운로드
    sample_urls = {
        "ballad": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "pop": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "rock": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "jazz": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
        "cinematic": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
    }
    sample_url = sample_urls.get(genre, sample_urls["ballad"])

    try:
        response = requests.get(sample_url, timeout=30)
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"  > Sample music saved: {output_path}")
    except Exception as e:
        print(f"  [ERROR] Failed to download sample music: {e}")

    return output_path


# ============================================================
# Video Service
# ============================================================

def split_into_scenes(summary: str, lyrics: str, num_scenes: int = 5):
    """스토리를 장면으로 분할"""
    sentences = summary.split('.')
    scenes = [s.strip() for s in sentences if s.strip()][:num_scenes]

    if len(scenes) < num_scenes:
        lyrics_lines = [l.strip() for l in lyrics.split('\n') if l.strip() and not l.startswith('[')]
        scenes.extend(lyrics_lines[:num_scenes - len(scenes)])

    return scenes[:num_scenes]


def generate_image_prompts(scenes: list, emotion: str):
    """각 장면에 대한 이미지 생성 프롬프트 생성"""
    emotion_styles = {
        "happy": "bright, cheerful, colorful, joyful atmosphere",
        "sad": "dark, melancholic, blue tones, rainy mood",
        "angry": "intense, red tones, dramatic lighting, powerful",
        "romantic": "soft, pink and purple hues, dreamy, intimate",
        "neutral": "balanced, natural colors, calm"
    }

    style = emotion_styles.get(emotion, emotion_styles["neutral"])
    return [f"{scene}, {style}, cinematic, high quality, detailed" for scene in scenes]


def generate_music_video(summary: str, emotion: str, lyrics: str, audio_path: str):
    """스토리와 음악을 바탕으로 뮤직비디오 생성"""
    import requests

    scenes = split_into_scenes(summary, lyrics)
    prompts = generate_image_prompts(scenes, emotion)

    output_path = f"./outputs/video_{uuid.uuid4()}.mp4"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"[VIDEO] Music video generation request:")
    print(f"  - Summary: {summary[:50]}...")
    print(f"  - Emotion: {emotion}")
    print(f"  - Scenes: {len(scenes)}")

    # 테스트용: 샘플 비디오 다운로드 (Cloudflare 무료 샘플)
    sample_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"

    try:
        response = requests.get(sample_url, timeout=30)
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"  > Sample video saved: {output_path}")
    except Exception as e:
        print(f"  [ERROR] Failed to download sample video: {e}")
        # 실패 시 빈 파일이라도 생성
        with open(output_path, "wb") as f:
            f.write(b"")

    return output_path


# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="찬호의 놀이터 API",
    description="AI 기반 창작 도구 API",
    version="1.0.0"
)

# outputs 폴더를 /files 경로로 서빙
outputs_dir = Path("./outputs")
outputs_dir.mkdir(exist_ok=True)
app.mount("/files", StaticFiles(directory=outputs_dir), name="files")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
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


# ============================================================
# Root & Health Endpoints
# ============================================================

@app.get("/")
async def root():
    return {
        "message": "찬호의 놀이터 API에 오신 것을 환영합니다!",
        "docs": "/docs",
        "version": "1.0.0",
        "endpoints": {
            "story_to_mv": "/api/story-to-mv/generate",
            "text_to_image": "/api/text-to-image/generate",
            "2d_to_3d": "/api/2d-to-3d/convert"
        }
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


# ============================================================
# Text to Image Endpoints
# ============================================================

@app.post("/api/text-to-image/generate", response_model=TextToImageResponse, tags=["Text to Image"])
async def generate_image_endpoint(
    prompt: str = Form(...),
    negative_prompt: str = Form(""),
    width: int = Form(512),
    height: int = Form(512),
    num_outputs: int = Form(1),
    provider: str = Form("replicate"),
    enhance: bool = Form(False)
):
    """텍스트로 이미지 생성"""
    try:
        print("\n[TEXT-TO-IMAGE] Generation Started")

        if num_outputs < 1 or num_outputs > 4:
            raise HTTPException(status_code=400, detail="num_outputs는 1-4 사이여야 합니다.")

        if width % 64 != 0 or height % 64 != 0:
            raise HTTPException(status_code=400, detail="width와 height는 64의 배수여야 합니다.")

        enhanced_prompt = None
        if enhance:
            enhanced_prompt = enhance_prompt(prompt)
            final_prompt = enhanced_prompt
        else:
            final_prompt = prompt

        image_paths = generate_image(
            prompt=final_prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_outputs=num_outputs,
            provider=provider
        )

        image_urls = [upload_s3(path) for path in image_paths]

        return TextToImageResponse(
            status="success",
            prompt=prompt,
            enhanced_prompt=enhanced_prompt,
            image_urls=image_urls,
            count=len(image_urls)
        )

    except Exception as e:
        error_msg = str(e)
        # 크레딧 부족 오류 확인
        if "402" in error_msg or "Insufficient credit" in error_msg or "credit" in error_msg.lower():
            raise HTTPException(status_code=402, detail="Replicate 크레딧이 부족합니다. https://replicate.com/account/billing 에서 크레딧을 충전해주세요.")
        elif "billing_hard_limit_reached" in error_msg or "Billing hard limit" in error_msg:
            raise HTTPException(status_code=402, detail="OpenAI 결제 한도에 도달했습니다. https://platform.openai.com/account/billing 에서 한도를 늘려주세요.")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/api/text-to-image/status", tags=["Text to Image"])
async def get_text_to_image_status():
    """서비스 상태 확인"""
    return {
        "service": "Text to Image",
        "status": "operational",
        "providers": {
            "replicate": os.getenv("REPLICATE_API_TOKEN") is not None,
            "stability": os.getenv("STABILITY_API_KEY") is not None,
            "dalle": os.getenv("OPENAI_API_KEY") is not None
        }
    }


# ============================================================
# 2D to 3D Endpoints
# ============================================================

class ConvertTo3DResponse(BaseModel):
    """2D to 3D 변환 응답"""
    status: str
    message: str
    original_filename: str
    preview_url: Optional[str] = None
    model_url: Optional[str] = None


@app.post("/api/2d-to-3d/convert", response_model=ConvertTo3DResponse, tags=["2D to 3D"])
async def convert_to_3d(
    file: UploadFile = File(...),
    prompt: str = Form("")
):
    """2D 이미지를 3D 모델로 변환 (Replicate TripoSR)"""
    import requests
    import base64

    print("\n[2D-TO-3D] Conversion Started")
    print(f"  - Filename: {file.filename}")
    if prompt:
        print(f"  - Prompt: {prompt}")

    # 업로드된 이미지 저장
    contents = await file.read()
    input_path = f"./outputs/input_{uuid.uuid4()}{Path(file.filename).suffix}"
    Path(input_path).parent.mkdir(parents=True, exist_ok=True)

    with open(input_path, "wb") as f:
        f.write(contents)
    print(f"  > Input saved: {input_path}")

    # Replicate API 키 확인
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        # 테스트 모드: 랜덤 이미지 반환
        print("  [WARNING] REPLICATE_API_TOKEN not set. Using test mode.")
        preview_path = f"./outputs/3d_preview_{uuid.uuid4()}.png"
        try:
            response = requests.get("https://picsum.photos/512/512", timeout=10)
            with open(preview_path, "wb") as f:
                f.write(response.content)
        except:
            preview_path = input_path

        return ConvertTo3DResponse(
            status="success",
            message="3D preview generated (test mode)",
            original_filename=file.filename,
            preview_url=upload_s3(preview_path),
            model_url=upload_s3(preview_path)
        )

    # 실제 Replicate TripoSR API 호출
    try:
        import replicate

        print("  > Calling Replicate TripoSR API...")

        # 이미지를 data URI로 변환
        with open(input_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # 파일 확장자에 따른 MIME 타입
        ext = Path(file.filename).suffix.lower()
        mime_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
        mime_type = mime_types.get(ext, "image/png")
        data_uri = f"data:{mime_type};base64,{image_data}"

        # TripoSR 모델 실행
        output = replicate.run(
            "camenduru/triposr:aecf62db-3e65-4268-9a0f-14dc9edf9042",
            input={
                "image": data_uri,
                "mc_resolution": 256,
                "foreground_ratio": 0.85
            }
        )

        # 결과 다운로드 (GLB 파일)
        model_path = f"./outputs/model_{uuid.uuid4()}.glb"
        if output:
            model_url = str(output)
            print(f"  > Downloading 3D model from: {model_url}")
            response = requests.get(model_url, timeout=60)
            with open(model_path, "wb") as f:
                f.write(response.content)
            print(f"  > Model saved: {model_path}")

            return ConvertTo3DResponse(
                status="success",
                message="3D model generated successfully!",
                original_filename=file.filename,
                preview_url=upload_s3(input_path),
                model_url=upload_s3(model_path)
            )
        else:
            raise Exception("No output from TripoSR")

    except Exception as e:
        error_msg = str(e)
        print(f"  [ERROR] 3D conversion failed: {error_msg}")

        # 크레딧 부족 오류 확인
        if "402" in error_msg or "Insufficient credit" in error_msg or "credit" in error_msg.lower():
            return ConvertTo3DResponse(
                status="error",
                message="Replicate 크레딧이 부족합니다. https://replicate.com/account/billing 에서 크레딧을 충전해주세요.",
                original_filename=file.filename,
                preview_url=upload_s3(input_path),
                model_url=None
            )

        # 기타 오류
        return ConvertTo3DResponse(
            status="error",
            message=f"3D 변환 실패: {error_msg}",
            original_filename=file.filename,
            preview_url=upload_s3(input_path),
            model_url=None
        )


@app.get("/api/2d-to-3d/status", tags=["2D to 3D"])
async def get_2d_to_3d_status():
    """서비스 상태 확인"""
    return {
        "service": "2D to 3D Conversion",
        "status": "operational",
        "provider": "Replicate TripoSR",
        "api_key_set": os.getenv("REPLICATE_API_TOKEN") is not None
    }


# ============================================================
# Story to MV Endpoints
# ============================================================

@app.post("/api/story-to-mv/generate", response_model=GenerateResponse, tags=["Story to MV"])
async def generate_story_to_mv(
    story: str = Form(...),
    genre: str = Form("ballad"),
    voice: str = Form("female")
):
    """스토리를 뮤직비디오로 변환"""
    try:
        print("\n" + "="*60)
        print("[STORY-TO-MV] Generation Started")
        print("="*60)

        # 1. Summary + Emotion Analysis
        print("\n[STEP 1] NLP: Analyzing story...")
        summary, emotion = summarize_and_emotion(story)
        print(f"  > Emotion: {emotion}")

        # 2. Lyrics Generation
        print("\n[STEP 2] NLP: Generating lyrics...")
        lyrics = generate_lyrics(summary, emotion)
        print(f"  > Lyrics generated ({len(lyrics)} chars)")

        # 3. Music Generation
        print("\n[STEP 3] Music: Generating AI music...")
        audio_path = generate_music(10, genre, voice, lyrics)
        print(f"  > Music generated: {audio_path}")

        # 4. Music Video Generation
        print("\n[STEP 4] Video: Generating music video...")
        video_path = generate_music_video(summary, emotion, lyrics, audio_path)
        print(f"  > Video generated: {video_path}")

        # 5. URL Generation
        print("\n[STEP 5] Storage: Generating URLs...")
        audio_url = upload_s3(audio_path)
        video_url = upload_s3(video_path)
        print(f"  > Audio URL: {audio_url}")
        print(f"  > Video URL: {video_url}")

        print("\n" + "="*60)
        print("[DONE] Generation Complete!")
        print("="*60 + "\n")

        return GenerateResponse(
            audio_url=audio_url,
            video_url=video_url,
            emotion=emotion,
            summary=summary,
            lyrics=lyrics
        )

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=f"뮤직비디오 생성 중 오류가 발생했습니다: {str(e)}")


@app.post("/api/story-to-mv/upload-story", tags=["Story to MV"])
async def upload_story(file: UploadFile = File(...)):
    """스토리 파일 업로드"""
    try:
        contents = await file.read()
        story_text = contents.decode('utf-8')

        return {
            "status": "success",
            "filename": file.filename,
            "story_length": len(story_text),
            "preview": story_text[:200] + "..." if len(story_text) > 200 else story_text,
            "message": "파일이 성공적으로 업로드되었습니다. 이제 Generate를 눌러주세요."
        }

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="UTF-8로 인코딩된 텍스트 파일만 지원합니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}")


@app.get("/api/story-to-mv/search-story/{keyword}", tags=["Story to MV"])
async def search_story(keyword: str):
    """키워드로 스토리 검색"""
    return {
        "status": "coming_soon",
        "keyword": keyword,
        "message": f"'{keyword}' 검색 기능은 현재 개발 중입니다.",
        "results": [],
        "suggestion": "직접 스토리를 입력해주세요."
    }


@app.get("/api/story-to-mv/status", tags=["Story to MV"])
async def get_story_to_mv_status():
    """서비스 상태 및 기능 확인"""
    return {
        "service": "Story to Music Video",
        "status": "operational",
        "version": "1.0.0",
        "features": {
            "story_analysis": {"status": "active", "description": "스토리 요약 및 감정 분석"},
            "lyrics_generation": {"status": "active", "description": "AI 가사 생성"},
            "music_generation": {"status": "stub", "description": "AI 음악 생성 (Suno AI 연동 예정)"},
            "video_generation": {"status": "stub", "description": "뮤직비디오 생성 (Runway 연동 예정)"},
            "file_upload": {"status": "active", "description": "텍스트 파일 업로드"},
            "story_search": {"status": "planned", "description": "웹에서 스토리 검색"}
        },
        "supported_formats": {
            "genres": ["ballad", "pop", "rock", "jazz", "cinematic"],
            "voices": ["female", "male"],
            "file_types": [".txt", ".md"]
        }
    }


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
