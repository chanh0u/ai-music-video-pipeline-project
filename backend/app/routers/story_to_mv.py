from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional

from app.schemas import (
    GenerateResponse,
    SessionCreateResponse,
    MVSession,
    StoryAnalyzeRequest,
    StoryAnalysisResult,
    LyricsResult,
    LyricsGenerateRequest,
    LyricsUpdateRequest,
    MusicResult,
    MusicGenerateRequest,
    SceneDescription,
    SceneImageResult,
    ImageGenerateRequest,
    SceneUpdateRequest,
    VideoClipResult,
    VideoClipGenerateRequest,
    FinalVideoResult,
    ComposeRequest
)
from app.services import nlp, music, video
from app.services.storage import upload_s3, get_local_url
from app.services import session as session_service

router = APIRouter()


# ========== 세션 관리 엔드포인트 ==========

@router.post("/session/create", response_model=SessionCreateResponse)
async def create_session():
    """
    새 MV Wizard 세션 생성

    Returns:
        session_id: 생성된 세션 ID
    """
    try:
        session_id = session_service.create_session()
        return SessionCreateResponse(
            session_id=session_id,
            message="세션이 생성되었습니다."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"세션 생성 실패: {str(e)}")


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    세션 조회

    Returns:
        MVSession: 세션 전체 상태
    """
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return session_data


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    success = session_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return {"message": "세션이 삭제되었습니다."}


# ========== Step 1: 스토리 분석 ==========

@router.post("/session/{session_id}/analyze")
async def analyze_story(session_id: str, request: StoryAnalyzeRequest):
    """
    Step 1: 스토리 분석

    - 스토리 요약
    - 감정 분석
    - 테마 추출
    - 장면 분할

    Returns:
        StoryAnalysisResult: 분석 결과
    """
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    try:
        print(f"\n[STEP 1] Story Analysis - Session: {session_id}")

        # 스토리 전체 분석
        analysis = nlp.analyze_story_full(request.story, request.num_scenes)

        # 세션 업데이트
        scenes_data = [
            {
                "index": s["index"],
                "description": s["description"],
                "prompt": s.get("prompt"),
                "duration": s.get("duration", 4.0)
            }
            for s in analysis["scenes"]
        ]

        session_service.update_session(session_id, {
            "story": request.story,
            "analysis": {
                "summary": analysis["summary"],
                "emotion": analysis["emotion"],
                "theme": analysis["theme"],
                "scenes": scenes_data
            },
            "scenes": scenes_data,
            "current_step": 2
        })

        return {
            "summary": analysis["summary"],
            "emotion": analysis["emotion"],
            "theme": analysis["theme"],
            "scenes": scenes_data
        }

    except Exception as e:
        print(f"[ERROR] Story analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"스토리 분석 실패: {str(e)}")


# ========== Step 2: 가사 생성 ==========

@router.post("/session/{session_id}/lyrics")
async def generate_lyrics(session_id: str, request: LyricsGenerateRequest = None):
    """
    Step 2: 가사 생성

    분석된 스토리를 바탕으로 가사 생성

    Returns:
        LyricsResult: 생성된 가사
    """
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    if session_data.get("analysis") is None:
        raise HTTPException(status_code=400, detail="먼저 스토리 분석을 완료해주세요.")

    try:
        print(f"\n[STEP 2] Lyrics Generation - Session: {session_id}")

        analysis = session_data["analysis"]
        summary = analysis.get("summary", "")
        emotion = analysis.get("emotion", "neutral")

        # 가사 생성
        lyrics = nlp.generate_lyrics(summary, emotion)

        # 세션 업데이트
        session_service.update_session(session_id, {
            "lyrics": {
                "lyrics": lyrics,
                "language": "ko"
            },
            "current_step": 3
        })

        return {
            "lyrics": lyrics,
            "language": "ko"
        }

    except Exception as e:
        print(f"[ERROR] Lyrics generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"가사 생성 실패: {str(e)}")


@router.put("/session/{session_id}/lyrics")
async def update_lyrics(session_id: str, request: LyricsUpdateRequest):
    """
    Step 2: 가사 수정

    사용자가 편집한 가사 저장

    Returns:
        LyricsResult: 수정된 가사
    """
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    try:
        session_service.update_session(session_id, {
            "lyrics": {
                "lyrics": request.lyrics,
                "language": "ko"
            }
        })

        return {
            "lyrics": request.lyrics,
            "language": "ko",
            "message": "가사가 수정되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가사 수정 실패: {str(e)}")


# ========== Step 3: 음악 생성 ==========

@router.post("/session/{session_id}/music")
async def generate_music_endpoint(session_id: str, request: MusicGenerateRequest = None):
    """
    Step 3: 음악 생성

    개발 모드: 샘플 음악 사용
    프로덕션: Suno AI 연동

    Returns:
        MusicResult: 생성된 음악 정보
    """
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    try:
        print(f"\n[STEP 3] Music Generation - Session: {session_id}")

        genre = request.genre if request else "ballad"
        duration = request.duration if request else 30.0
        lyrics = session_data.get("lyrics", {}).get("lyrics", "")

        # 음악 생성 (샘플 또는 AI)
        music_result = music.generate_music_for_wizard(genre, duration, lyrics)

        # URL 생성
        audio_url = get_local_url(music_result["audio_path"])

        # 세션 업데이트
        session_service.update_session(session_id, {
            "music": {
                "audio_url": audio_url,
                "audio_path": music_result["audio_path"],
                "duration": music_result["duration"],
                "genre": music_result["genre"],
                "sample_name": music_result.get("sample_name")
            },
            "current_step": 4
        })

        return {
            "audio_url": audio_url,
            "duration": music_result["duration"],
            "genre": music_result["genre"],
            "sample_name": music_result.get("sample_name")
        }

    except Exception as e:
        print(f"[ERROR] Music generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"음악 생성 실패: {str(e)}")


# ========== Step 4: 이미지 생성 ==========

@router.post("/session/{session_id}/images")
async def generate_images(session_id: str, request: ImageGenerateRequest = None):
    """
    Step 4: 전체 장면 이미지 생성

    각 장면의 프롬프트를 바탕으로 9:16 이미지 생성

    Returns:
        list[SceneImageResult]: 생성된 이미지 목록
    """
    from app.services import image as image_service

    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    scenes = session_data.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="먼저 스토리 분석을 완료해주세요.")

    try:
        print(f"\n[STEP 4] Image Generation - Session: {session_id}")

        style = request.style if request else "cinematic"

        # 이미지 생성
        image_results = image_service.generate_scene_images(
            scenes=scenes,
            style=style,
            session_id=session_id
        )

        # URL 변환
        images_data = []
        for result in image_results:
            image_url = get_local_url(result["image_path"])
            images_data.append({
                "index": result["index"],
                "image_url": image_url,
                "image_path": result["image_path"],
                "prompt": result["prompt"]
            })

        # 세션 업데이트
        session_service.update_session(session_id, {
            "images": images_data,
            "current_step": 5
        })

        return images_data

    except Exception as e:
        print(f"[ERROR] Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"이미지 생성 실패: {str(e)}")


@router.post("/session/{session_id}/images/{index}")
async def regenerate_image(session_id: str, index: int, request: ImageGenerateRequest = None):
    """
    Step 4: 단일 이미지 재생성

    특정 장면의 이미지만 다시 생성

    Returns:
        SceneImageResult: 재생성된 이미지
    """
    from app.services import image as image_service

    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    scenes = session_data.get("scenes", [])
    if index >= len(scenes):
        raise HTTPException(status_code=404, detail="장면을 찾을 수 없습니다.")

    try:
        print(f"\n[STEP 4] Regenerate Image {index} - Session: {session_id}")

        scene = scenes[index]
        style = request.style if request else "cinematic"

        # 이미지 재생성
        image_path = image_service.generate_shorts_image(
            prompt=scene.get("prompt", scene.get("description", "")),
            style=style,
            session_id=session_id,
            scene_index=index
        )

        image_url = get_local_url(image_path)

        # 세션 업데이트 (해당 인덱스만)
        images = session_data.get("images", [])
        while len(images) <= index:
            images.append(None)

        images[index] = {
            "index": index,
            "image_url": image_url,
            "image_path": image_path,
            "prompt": scene.get("prompt", "")
        }

        session_service.update_session(session_id, {"images": images})

        return images[index]

    except Exception as e:
        print(f"[ERROR] Image regeneration failed: {e}")
        raise HTTPException(status_code=500, detail=f"이미지 재생성 실패: {str(e)}")


@router.put("/session/{session_id}/scenes/{index}")
async def update_scene_prompt(session_id: str, index: int, request: SceneUpdateRequest):
    """
    Step 4: 장면 프롬프트 수정

    사용자가 프롬프트를 직접 편집

    Returns:
        SceneDescription: 수정된 장면 정보
    """
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    scenes = session_data.get("scenes", [])
    if index >= len(scenes):
        raise HTTPException(status_code=404, detail="장면을 찾을 수 없습니다.")

    try:
        scenes[index]["prompt"] = request.prompt

        session_service.update_session(session_id, {"scenes": scenes})

        return {
            "index": index,
            "description": scenes[index].get("description"),
            "prompt": request.prompt,
            "message": "프롬프트가 수정되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프롬프트 수정 실패: {str(e)}")


# ========== Step 5: 비디오 클립 생성 ==========

@router.post("/session/{session_id}/video-clips")
async def generate_video_clips(session_id: str, request: VideoClipGenerateRequest = None):
    """
    Step 5: 전체 비디오 클립 생성

    각 장면 이미지를 비디오 클립으로 변환 (Stable Video Diffusion)

    Returns:
        list[VideoClipResult]: 생성된 비디오 클립 목록
    """
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    images = session_data.get("images", [])
    if not images:
        raise HTTPException(status_code=400, detail="먼저 이미지 생성을 완료해주세요.")

    try:
        print(f"\n[STEP 5] Video Clip Generation - Session: {session_id}")

        motion_strength = request.motion_strength if request else 0.5

        # 비디오 클립 생성
        clips_data = []
        for img_data in images:
            clip_result = video.image_to_video_svd(
                image_path=img_data.get("image_path"),
                duration=4.0,
                motion_strength=motion_strength,
                session_id=session_id,
                scene_index=img_data.get("index", 0)
            )

            video_url = get_local_url(clip_result["video_path"])
            clips_data.append({
                "index": img_data.get("index", len(clips_data)),
                "video_url": video_url,
                "video_path": clip_result["video_path"],
                "duration": clip_result["duration"]
            })

        # 세션 업데이트
        session_service.update_session(session_id, {
            "video_clips": clips_data,
            "current_step": 6
        })

        return clips_data

    except Exception as e:
        print(f"[ERROR] Video clip generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"비디오 클립 생성 실패: {str(e)}")


@router.post("/session/{session_id}/video-clips/{index}")
async def regenerate_video_clip(session_id: str, index: int, request: VideoClipGenerateRequest = None):
    """
    Step 5: 단일 비디오 클립 재생성

    특정 장면의 비디오 클립만 다시 생성

    Returns:
        VideoClipResult: 재생성된 비디오 클립
    """
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    images = session_data.get("images", [])
    if index >= len(images):
        raise HTTPException(status_code=404, detail="장면을 찾을 수 없습니다.")

    try:
        print(f"\n[STEP 5] Regenerate Video Clip {index} - Session: {session_id}")

        motion_strength = request.motion_strength if request else 0.5
        img_data = images[index]

        # 비디오 클립 재생성
        clip_result = video.image_to_video_svd(
            image_path=img_data.get("image_path"),
            duration=4.0,
            motion_strength=motion_strength,
            session_id=session_id,
            scene_index=index
        )

        video_url = get_local_url(clip_result["video_path"])

        # 세션 업데이트
        clips = session_data.get("video_clips", [])
        while len(clips) <= index:
            clips.append(None)

        clips[index] = {
            "index": index,
            "video_url": video_url,
            "video_path": clip_result["video_path"],
            "duration": clip_result["duration"]
        }

        session_service.update_session(session_id, {"video_clips": clips})

        return clips[index]

    except Exception as e:
        print(f"[ERROR] Video clip regeneration failed: {e}")
        raise HTTPException(status_code=500, detail=f"비디오 클립 재생성 실패: {str(e)}")


# ========== Step 6: 최종 합성 ==========

@router.post("/session/{session_id}/compose")
async def compose_final_video(session_id: str, request: ComposeRequest = None):
    """
    Step 6: 최종 비디오 합성

    모든 비디오 클립 + 음악을 합성하여 최종 뮤직비디오 생성

    Returns:
        FinalVideoResult: 최종 비디오 정보
    """
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    video_clips = session_data.get("video_clips", [])
    music_data = session_data.get("music", {})

    if not video_clips:
        raise HTTPException(status_code=400, detail="먼저 비디오 클립 생성을 완료해주세요.")
    if not music_data:
        raise HTTPException(status_code=400, detail="먼저 음악 생성을 완료해주세요.")

    try:
        print(f"\n[STEP 6] Final Video Composition - Session: {session_id}")

        add_subtitles = request.add_subtitles if request else False
        lyrics = session_data.get("lyrics", {}).get("lyrics", "") if add_subtitles else ""

        # 클립 경로 리스트
        clip_paths = [clip.get("video_path") for clip in video_clips if clip]
        audio_path = music_data.get("audio_path")

        # 최종 합성
        final_result = video.compose_clips_with_audio(
            clips=clip_paths,
            audio_path=audio_path,
            session_id=session_id,
            lyrics=lyrics if add_subtitles else None
        )

        video_url = get_local_url(final_result["video_path"])

        # 세션 업데이트
        session_service.update_session(session_id, {
            "final_video": {
                "video_url": video_url,
                "video_path": final_result["video_path"],
                "duration": final_result["duration"],
                "resolution": final_result.get("resolution", "1080x1920")
            }
        })

        return {
            "video_url": video_url,
            "duration": final_result["duration"],
            "resolution": final_result.get("resolution", "1080x1920")
        }

    except Exception as e:
        print(f"[ERROR] Final composition failed: {e}")
        raise HTTPException(status_code=500, detail=f"최종 합성 실패: {str(e)}")


@router.get("/session/{session_id}/download")
async def download_final_video(session_id: str):
    """
    Step 6: 최종 비디오 다운로드

    Returns:
        FileResponse: 비디오 파일
    """
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    final_video = session_data.get("final_video", {})
    video_path = final_video.get("video_path")

    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="다운로드할 비디오가 없습니다.")

    return FileResponse(
        path=video_path,
        filename=f"mv_{session_id[:8]}.mp4",
        media_type="video/mp4"
    )


# ========== 레거시 엔드포인트 ==========

@router.post("/generate", response_model=GenerateResponse)
async def generate_music_video(
    story: str = Form(...),
    genre: str = Form("ballad"),
    voice: str = Form("female")
):
    """
    스토리를 뮤직비디오로 변환
    
    전체 프로세스:
    1. NLP: 스토리 요약 + 감정 분석
    2. NLP: 가사 생성
    3. Music: AI 음악 생성
    4. Video: 이미지 생성 + 비디오 합성
    5. Storage: 파일 저장 및 URL 반환
    
    Parameters:
    - story: 스토리 텍스트 (필수)
    - genre: 음악 장르 (ballad, pop, rock, jazz, cinematic)
    - voice: 보이스 타입 (female, male)
    
    Returns:
    - audio_url: 생성된 음악 URL
    - video_url: 생성된 뮤직비디오 URL
    - emotion: 감정 분석 결과
    - summary: 스토리 요약
    - lyrics: 생성된 가사
    """
    
    try:
        print("\n" + "="*60)
        print("🎬 Story to Music Video Generation Started")
        print("="*60)
        
        # 1. 요약 + 감정 분석
        print("\n[STEP 1] NLP: 스토리 분석 중...")
        summary, emotion = nlp.summarize_and_emotion(story)
        print(f"  ✓ 요약: {summary[:50]}...")
        print(f"  ✓ 감정: {emotion}")
        
        # 2. 가사 생성
        print("\n[STEP 2] NLP: 가사 생성 중...")
        lyrics = nlp.generate_lyrics(summary, emotion)
        print(f"  ✓ 가사 생성 완료 ({len(lyrics)} chars)")
        
        # 3. 음악 생성 (기본 10초)
        print("\n[STEP 3] Music: AI 음악 생성 중...")
        audio_path = music.generate_music(10, genre, voice, lyrics)
        print(f"  ✓ 음악 생성 완료: {audio_path}")
        
        # 4. 뮤직비디오 생성
        print("\n[STEP 4] Video: 뮤직비디오 생성 중...")
        video_path = video.generate_music_video(
            summary=summary,
            emotion=emotion,
            lyrics=lyrics,
            audio_path=audio_path
        )
        print(f"  ✓ 비디오 생성 완료: {video_path}")
        
        # 5. URL 생성 (S3 업로드 또는 로컬 URL)
        print("\n[STEP 5] Storage: URL 생성 중...")
        audio_url = upload_s3(audio_path)
        video_url = upload_s3(video_path)
        print(f"  ✓ Audio URL: {audio_url}")
        print(f"  ✓ Video URL: {video_url}")
        
        print("\n" + "="*60)
        print("✅ Generation Complete!")
        print("="*60 + "\n")
        
        return GenerateResponse(
            audio_url=audio_url,
            video_url=video_url,
            emotion=emotion,
            summary=summary,
            lyrics=lyrics
        )
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"뮤직비디오 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/upload-story")
async def upload_story(file: UploadFile = File(...)):
    """
    스토리 파일 업로드
    
    지원 형식: .txt, .md
    """
    try:
        # 파일 읽기
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
        raise HTTPException(
            status_code=400,
            detail="UTF-8로 인코딩된 텍스트 파일만 지원합니다."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/search-story/{keyword}")
async def search_story(keyword: str):
    """
    키워드로 스토리 검색 (나무위키, 위키피디아 등)
    
    TODO: 웹 크롤링 구현
    """
    # TODO: 나무위키, 위키피디아 API 또는 크롤링
    # import requests
    # from bs4 import BeautifulSoup
    
    return {
        "status": "coming_soon",
        "keyword": keyword,
        "message": f"'{keyword}' 검색 기능은 현재 개발 중입니다.",
        "results": [],
        "suggestion": "직접 스토리를 입력해주세요."
    }


@router.get("/status")
async def get_status():
    """서비스 상태 및 기능 확인"""
    return {
        "service": "Story to Music Video",
        "status": "operational",
        "version": "1.0.0",
        "features": {
            "story_analysis": {
                "status": "active",
                "description": "스토리 요약 및 감정 분석"
            },
            "lyrics_generation": {
                "status": "active", 
                "description": "AI 가사 생성"
            },
            "music_generation": {
                "status": "stub",
                "description": "AI 음악 생성 (Suno AI 연동 예정)"
            },
            "video_generation": {
                "status": "stub",
                "description": "뮤직비디오 생성 (Runway 연동 예정)"
            },
            "file_upload": {
                "status": "active",
                "description": "텍스트 파일 업로드"
            },
            "story_search": {
                "status": "planned",
                "description": "웹에서 스토리 검색"
            }
        },
        "supported_formats": {
            "genres": ["ballad", "pop", "rock", "jazz", "cinematic"],
            "voices": ["female", "male"],
            "file_types": [".txt", ".md"]
        }
    }
