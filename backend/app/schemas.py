from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class GenerateResponse(BaseModel):
    """Story to MV 생성 응답 (레거시)"""
    audio_url: str
    video_url: str
    emotion: str
    summary: Optional[str] = None
    lyrics: Optional[str] = None


# ========== MV Wizard 스키마 ==========

class SceneDescription(BaseModel):
    """장면 설명"""
    index: int
    description: str
    prompt: Optional[str] = None
    duration: float = 4.0  # 초


class StoryAnalysisResult(BaseModel):
    """Step 1: 스토리 분석 결과"""
    summary: str
    emotion: str
    theme: str
    scenes: List[SceneDescription]


class LyricsResult(BaseModel):
    """Step 2: 가사 생성 결과"""
    lyrics: str
    language: str = "ko"


class MusicResult(BaseModel):
    """Step 3: 음악 생성 결과"""
    audio_url: str
    duration: float
    genre: str
    sample_name: Optional[str] = None


class SceneImageResult(BaseModel):
    """Step 4: 장면 이미지 생성 결과"""
    index: int
    image_url: str
    prompt: str


class VideoClipResult(BaseModel):
    """Step 5: 비디오 클립 생성 결과"""
    index: int
    video_url: str
    duration: float


class FinalVideoResult(BaseModel):
    """Step 6: 최종 비디오 결과"""
    video_url: str
    duration: float
    resolution: str = "1080x1920"  # 9:16 Shorts


class YouTubeUploadResult(BaseModel):
    """YouTube 업로드 결과"""
    video_id: str
    url: str
    title: str
    status: str


class MVSession(BaseModel):
    """MV Wizard 세션 전체 상태"""
    session_id: str
    created_at: str
    updated_at: str
    current_step: int = 1
    story: Optional[str] = None
    analysis: Optional[StoryAnalysisResult] = None
    lyrics: Optional[LyricsResult] = None
    music: Optional[MusicResult] = None
    scenes: List[SceneDescription] = []
    images: List[SceneImageResult] = []
    video_clips: List[VideoClipResult] = []
    final_video: Optional[FinalVideoResult] = None
    youtube: Optional[YouTubeUploadResult] = None


# ========== API Request/Response 스키마 ==========

class SessionCreateResponse(BaseModel):
    """세션 생성 응답"""
    session_id: str
    message: str


class StoryAnalyzeRequest(BaseModel):
    """Step 1: 스토리 분석 요청"""
    story: str
    num_scenes: int = 5


class LyricsGenerateRequest(BaseModel):
    """Step 2: 가사 생성 요청"""
    style: Optional[str] = None  # ballad, pop, rock, etc.


class LyricsUpdateRequest(BaseModel):
    """Step 2: 가사 수정 요청"""
    lyrics: str


class MusicGenerateRequest(BaseModel):
    """Step 3: 음악 생성 요청"""
    genre: str = "ballad"
    duration: float = 30.0


class ImageGenerateRequest(BaseModel):
    """Step 4: 이미지 생성 요청"""
    style: Optional[str] = None  # anime, realistic, etc.


class SceneUpdateRequest(BaseModel):
    """Step 4: 장면 프롬프트 수정 요청"""
    prompt: str


class VideoClipGenerateRequest(BaseModel):
    """Step 5: 비디오 클립 생성 요청"""
    motion_strength: float = 0.5  # 0.0 ~ 1.0


class ComposeRequest(BaseModel):
    """Step 6: 최종 합성 요청"""
    add_subtitles: bool = False


class YouTubeUploadRequest(BaseModel):
    """YouTube 업로드 요청"""
    title: str
    description: Optional[str] = None
    tags: List[str] = []
    privacy: str = "private"  # private, unlisted, public
