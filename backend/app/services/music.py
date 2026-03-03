# app/services/music.py
"""
Music 서비스 - AI 음악 생성

실제 구현 시:
- Suno AI API
- MusicGen (Meta)
- AudioCraft
"""
from pathlib import Path
import uuid

def generate_music(duration: int, genre: str, voice: str, lyrics: str):
    """
    AI로 음악 생성
    
    Args:
        duration: 음악 길이 (초)
        genre: 음악 장르 (ballad, pop, rock, jazz, cinematic)
        voice: 보이스 타입 (female, male)
        lyrics: 가사
        
    Returns:
        str: 생성된 음악 파일 경로
    """
    # TODO: Suno AI 또는 MusicGen API 호출
    # import requests
    # response = requests.post(
    #     "https://api.suno.ai/v1/generate",
    #     json={
    #         "lyrics": lyrics,
    #         "genre": genre,
    #         "voice": voice,
    #         "duration": duration
    #     },
    #     headers={"Authorization": f"Bearer {SUNO_API_KEY}"}
    # )
    # audio_url = response.json()["audio_url"]
    # 
    # # 다운로드 및 저장
    # audio_data = requests.get(audio_url).content
    # output_path = f"./outputs/{uuid.uuid4()}.mp3"
    # with open(output_path, "wb") as f:
    #     f.write(audio_data)
    
    # 임시 구현 - 실제 파일 생성 없이 경로만 반환
    output_path = f"./outputs/music_{uuid.uuid4()}.mp3"
    
    # 실제 환경에서는 여기서 음악 파일 생성
    print(f"[MUSIC] 음악 생성 요청:")
    print(f"  - Duration: {duration}초")
    print(f"  - Genre: {genre}")
    print(f"  - Voice: {voice}")
    print(f"  - Lyrics length: {len(lyrics)} chars")
    print(f"  - Output: {output_path}")
    
    return output_path


def create_silent_audio(duration: int = 10):
    """
    테스트용 무음 오디오 생성 (선택사항)

    Args:
        duration: 오디오 길이 (초)

    Returns:
        str: 생성된 오디오 파일 경로
    """
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine

        # 무음 생성
        silent = AudioSegment.silent(duration=duration * 1000)

        # 저장
        output_path = f"./outputs/silent_{uuid.uuid4()}.mp3"
        silent.export(output_path, format="mp3")

        return output_path
    except ImportError:
        print("[WARNING] pydub not installed. Returning mock path.")
        return f"./outputs/silent_{uuid.uuid4()}.mp3"


# ========== MV Wizard 용 샘플 음악 ==========

# 장르별 샘플 음악 URL (무료 로열티 프리 음원 사용)
# 실제 서비스에서는 Suno AI로 대체
SAMPLE_MUSIC = {
    "ballad": {
        "url": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
        "name": "Emotional Piano Ballad",
        "duration": 30.0
    },
    "pop": {
        "url": "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c8c8a73467.mp3",
        "name": "Upbeat Pop",
        "duration": 30.0
    },
    "rock": {
        "url": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6ff1bab.mp3",
        "name": "Energetic Rock",
        "duration": 30.0
    },
    "jazz": {
        "url": "https://cdn.pixabay.com/download/audio/2022/08/02/audio_884fe92c21.mp3",
        "name": "Smooth Jazz",
        "duration": 30.0
    },
    "cinematic": {
        "url": "https://cdn.pixabay.com/download/audio/2022/02/22/audio_d1718ab41b.mp3",
        "name": "Cinematic Epic",
        "duration": 30.0
    }
}


def get_sample_music(genre: str = "ballad", duration: float = 30.0) -> dict:
    """
    개발용 샘플 음악 반환

    Args:
        genre: 음악 장르 (ballad, pop, rock, jazz, cinematic)
        duration: 요청 길이 (참고용)

    Returns:
        dict: {audio_url, duration, genre, sample_name}
    """
    sample = SAMPLE_MUSIC.get(genre, SAMPLE_MUSIC["ballad"])

    # 샘플 다운로드 및 로컬 저장
    import requests
    import os

    output_dir = Path("./outputs/samples")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"sample_{genre}.mp3"

    # 캐시된 파일이 없으면 다운로드
    if not output_path.exists():
        try:
            print(f"[MUSIC] Downloading sample music: {sample['name']}")
            response = requests.get(sample["url"], timeout=30)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"[MUSIC] Sample saved: {output_path}")
            else:
                print(f"[MUSIC] Download failed: {response.status_code}")
                # 다운로드 실패시 무음 생성
                return {
                    "audio_url": create_silent_audio(int(duration)),
                    "duration": duration,
                    "genre": genre,
                    "sample_name": "Silent (fallback)"
                }
        except Exception as e:
            print(f"[MUSIC] Download error: {e}")
            return {
                "audio_url": create_silent_audio(int(duration)),
                "duration": duration,
                "genre": genre,
                "sample_name": "Silent (fallback)"
            }

    print(f"[MUSIC] Using sample: {sample['name']} ({genre})")

    return {
        "audio_path": str(output_path),
        "duration": sample["duration"],
        "genre": genre,
        "sample_name": sample["name"]
    }


def generate_music_for_wizard(genre: str = "ballad", duration: float = 30.0, lyrics: str = "") -> dict:
    """
    MV Wizard용 음악 생성 (개발: 샘플, 프로덕션: Suno AI)

    Args:
        genre: 음악 장르
        duration: 음악 길이
        lyrics: 가사 (Suno AI 사용시)

    Returns:
        dict: 음악 정보
    """
    import os

    # Suno API 키가 있으면 실제 생성
    suno_api_key = os.getenv("SUNO_API_KEY")
    if suno_api_key:
        # TODO: Suno AI API 호출
        pass

    # 개발 모드: 샘플 음악 사용
    return get_sample_music(genre, duration)
