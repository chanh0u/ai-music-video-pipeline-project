# app/services/video.py
"""
Video 서비스 - AI 뮤직비디오 생성

실제 구현 시:
- Runway Gen-2
- Stable Video Diffusion
- Pika Labs
- FFmpeg (이미지 → 비디오)
"""
from pathlib import Path
import uuid

def generate_music_video(
    summary: str,
    emotion: str,
    lyrics: str,
    audio_path: str
):
    """
    스토리와 음악을 바탕으로 뮤직비디오 생성
    
    프로세스:
    1. 스토리를 장면별로 분할
    2. 각 장면에 대한 이미지 생성 (Stable Diffusion)
    3. 이미지들을 비디오로 합성 (FFmpeg)
    4. 오디오와 비디오 결합
    
    Args:
        summary: 스토리 요약
        emotion: 감정
        lyrics: 가사
        audio_path: 오디오 파일 경로
        
    Returns:
        str: 생성된 비디오 파일 경로
    """
    # TODO: 실제 비디오 생성 파이프라인
    
    # 1. 스토리를 장면으로 분할
    scenes = split_into_scenes(summary, lyrics)
    
    # 2. 각 장면에 대한 프롬프트 생성
    prompts = generate_image_prompts(scenes, emotion)
    
    # 3. 이미지 생성
    # images = generate_images(prompts)
    
    # 4. 이미지 → 비디오 (FFmpeg)
    # video_path = images_to_video(images)
    
    # 5. 오디오 + 비디오 합성
    # final_video = merge_audio_video(video_path, audio_path)
    
    # 임시 구현
    output_path = f"./outputs/video_{uuid.uuid4()}.mp4"
    
    print(f"[VIDEO] 뮤직비디오 생성 요청:")
    print(f"  - Summary: {summary[:50]}...")
    print(f"  - Emotion: {emotion}")
    print(f"  - Scenes: {len(scenes)}")
    print(f"  - Audio: {audio_path}")
    print(f"  - Output: {output_path}")
    
    return output_path


def split_into_scenes(summary: str, lyrics: str, num_scenes: int = 5):
    """
    스토리를 장면으로 분할
    
    Args:
        summary: 스토리 요약
        lyrics: 가사
        num_scenes: 생성할 장면 수
        
    Returns:
        list: 장면 설명 리스트
    """
    # TODO: Claude API로 장면 분할
    # "이 스토리를 {num_scenes}개의 시각적 장면으로 나눠주세요"
    
    # 임시 구현
    sentences = summary.split('.')
    scenes = [s.strip() for s in sentences if s.strip()][:num_scenes]
    
    if len(scenes) < num_scenes:
        # 가사에서 추가
        lyrics_lines = [l.strip() for l in lyrics.split('\n') if l.strip() and not l.startswith('[')]
        scenes.extend(lyrics_lines[:num_scenes - len(scenes)])
    
    return scenes[:num_scenes]


def generate_image_prompts(scenes: list, emotion: str):
    """
    각 장면에 대한 이미지 생성 프롬프트 생성
    
    Args:
        scenes: 장면 설명 리스트
        emotion: 감정
        
    Returns:
        list: 프롬프트 리스트
    """
    emotion_styles = {
        "happy": "bright, cheerful, colorful, joyful atmosphere",
        "sad": "dark, melancholic, blue tones, rainy mood",
        "angry": "intense, red tones, dramatic lighting, powerful",
        "romantic": "soft, pink and purple hues, dreamy, intimate",
        "neutral": "balanced, natural colors, calm"
    }
    
    style = emotion_styles.get(emotion, emotion_styles["neutral"])
    
    prompts = []
    for scene in scenes:
        prompt = f"{scene}, {style}, cinematic, high quality, detailed"
        prompts.append(prompt)
    
    return prompts


def generate_images(prompts: list):
    """
    프롬프트로 이미지 생성
    
    Args:
        prompts: 프롬프트 리스트
        
    Returns:
        list: 생성된 이미지 경로 리스트
    """
    # TODO: Stable Diffusion API 호출
    # import replicate
    # output = replicate.run(
    #     "stability-ai/stable-diffusion",
    #     input={"prompt": prompt}
    # )
    
    image_paths = []
    for i, prompt in enumerate(prompts):
        image_path = f"./outputs/scene_{i}_{uuid.uuid4()}.png"
        image_paths.append(image_path)
        print(f"  [IMAGE {i+1}] {prompt[:50]}...")
    
    return image_paths


def images_to_video(image_paths: list, fps: int = 1):
    """
    이미지들을 비디오로 변환 (FFmpeg)
    
    Args:
        image_paths: 이미지 경로 리스트
        fps: 초당 프레임 수
        
    Returns:
        str: 생성된 비디오 경로
    """
    # TODO: FFmpeg 실행
    # import subprocess
    # output_path = f"./outputs/temp_{uuid.uuid4()}.mp4"
    # subprocess.run([
    #     "ffmpeg",
    #     "-framerate", str(fps),
    #     "-i", "scene_%d.png",
    #     "-c:v", "libx264",
    #     "-pix_fmt", "yuv420p",
    #     output_path
    # ])
    
    output_path = f"./outputs/temp_{uuid.uuid4()}.mp4"
    return output_path


def merge_audio_video(video_path: str, audio_path: str):
    """
    비디오와 오디오 합성

    Args:
        video_path: 비디오 경로
        audio_path: 오디오 경로

    Returns:
        str: 최종 비디오 경로
    """
    # TODO: FFmpeg으로 합성
    # import subprocess
    # output_path = f"./outputs/final_{uuid.uuid4()}.mp4"
    # subprocess.run([
    #     "ffmpeg",
    #     "-i", video_path,
    #     "-i", audio_path,
    #     "-c:v", "copy",
    #     "-c:a", "aac",
    #     "-shortest",
    #     output_path
    # ])

    output_path = f"./outputs/final_{uuid.uuid4()}.mp4"
    return output_path


# ========== MV Wizard 용 비디오 생성 ==========

import os


def image_to_video_svd(
    image_path: str,
    duration: float = 4.0,
    motion_strength: float = 0.5,
    session_id: str = None,
    scene_index: int = 0
) -> dict:
    """
    Stable Video Diffusion으로 이미지를 비디오로 변환

    Args:
        image_path: 입력 이미지 경로
        duration: 비디오 길이 (초)
        motion_strength: 모션 강도 (0.0 ~ 1.0)
        session_id: 세션 ID
        scene_index: 장면 인덱스

    Returns:
        dict: {video_path, duration}
    """
    import os

    # Replicate API 키 확인
    api_key = os.getenv("REPLICATE_API_TOKEN")

    if api_key and Path(image_path).exists():
        try:
            import replicate
            import requests

            print(f"[VIDEO] SVD - Processing scene {scene_index}")

            # 이미지 파일 읽기
            with open(image_path, "rb") as f:
                image_data = f.read()

            # Stable Video Diffusion 실행
            # 모델: stability-ai/stable-video-diffusion
            output = replicate.run(
                "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
                input={
                    "input_image": f"data:image/png;base64,{__import__('base64').b64encode(image_data).decode()}",
                    "motion_bucket_id": int(motion_strength * 255),
                    "fps": 8,
                    "num_frames": int(duration * 8)  # 8fps * duration
                }
            )

            # 결과 다운로드
            if output:
                video_url = str(output)
                response = requests.get(video_url)

                output_dir = Path("./outputs/clips")
                output_dir.mkdir(parents=True, exist_ok=True)

                filename = f"clip_{scene_index}_{session_id[:8] if session_id else uuid.uuid4()}.mp4"
                output_path = output_dir / filename

                with open(output_path, "wb") as f:
                    f.write(response.content)

                print(f"[VIDEO] SVD complete: {output_path}")
                return {
                    "video_path": str(output_path),
                    "duration": duration
                }

        except Exception as e:
            print(f"[ERROR] SVD failed: {e}")
            # 실패시 플레이스홀더 생성

    # 개발 모드: 플레이스홀더 비디오 생성
    return create_placeholder_video(session_id, scene_index, duration)


def create_placeholder_video(
    session_id: str = None,
    scene_index: int = 0,
    duration: float = 4.0
) -> dict:
    """
    개발용 플레이스홀더 비디오 생성

    이미지를 비디오로 변환하거나, 컬러 배경 비디오 생성

    Args:
        session_id: 세션 ID
        scene_index: 장면 인덱스
        duration: 비디오 길이

    Returns:
        dict: {video_path, duration}
    """
    output_dir = Path("./outputs/clips")
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"clip_{scene_index}_{session_id[:8] if session_id else uuid.uuid4()}.mp4"
    output_path = output_dir / filename

    # FFmpeg가 설치되어 있는지 확인
    try:
        import subprocess

        # 컬러 팔레트
        colors = ["#667eea", "#764ba2", "#f0932b", "#2ecc71", "#e74c3c"]
        color = colors[scene_index % len(colors)]

        # 9:16 사이즈 비디오 생성
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:s=540x960:d={duration}",
            "-vf", f"drawtext=text='Scene {scene_index + 1}':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[VIDEO] Placeholder created: {output_path}")
            return {
                "video_path": str(output_path),
                "duration": duration
            }
        else:
            print(f"[WARNING] FFmpeg failed: {result.stderr}")

    except FileNotFoundError:
        print("[WARNING] FFmpeg not installed")
    except Exception as e:
        print(f"[WARNING] Placeholder creation failed: {e}")

    # FFmpeg 실패시 빈 경로 반환
    print(f"[VIDEO] Mock video path: {output_path}")
    return {
        "video_path": str(output_path),
        "duration": duration
    }


def compose_clips_with_audio(
    clips: list,
    audio_path: str,
    session_id: str = None,
    lyrics: str = None
) -> dict:
    """
    비디오 클립들과 오디오를 합성하여 최종 비디오 생성

    Args:
        clips: 비디오 클립 경로 리스트
        audio_path: 오디오 파일 경로
        session_id: 세션 ID
        lyrics: 자막용 가사 (선택)

    Returns:
        dict: {video_path, duration, resolution}
    """
    output_dir = Path("./outputs/final")
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"mv_{session_id[:8] if session_id else uuid.uuid4()}.mp4"
    output_path = output_dir / filename

    # 존재하는 클립만 필터링
    valid_clips = [c for c in clips if c and Path(c).exists()]

    if not valid_clips:
        print("[WARNING] No valid video clips found")
        # 빈 비디오 생성
        return create_placeholder_video(session_id, 0, 30.0)

    try:
        import subprocess

        # 클립 리스트 파일 생성
        concat_file = output_dir / f"concat_{session_id[:8] if session_id else uuid.uuid4()}.txt"
        with open(concat_file, "w") as f:
            for clip in valid_clips:
                f.write(f"file '{Path(clip).absolute()}'\n")

        # 1. 비디오 클립 연결
        temp_video = output_dir / f"temp_{uuid.uuid4()}.mp4"
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(temp_video)
        ]

        result = subprocess.run(concat_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[WARNING] Concat failed: {result.stderr}")
            # 실패시 첫 번째 클립 사용
            temp_video = Path(valid_clips[0])

        # 2. 오디오 합성
        if audio_path and Path(audio_path).exists():
            merge_cmd = [
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(output_path)
            ]

            result = subprocess.run(merge_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[WARNING] Audio merge failed: {result.stderr}")
                # 실패시 비디오만 복사
                import shutil
                shutil.copy(temp_video, output_path)
        else:
            # 오디오 없이 비디오만
            import shutil
            shutil.copy(temp_video, output_path)

        # 임시 파일 정리
        if concat_file.exists():
            concat_file.unlink()
        if temp_video.exists() and temp_video != Path(valid_clips[0]):
            temp_video.unlink()

        # 비디오 정보 조회
        duration = len(valid_clips) * 4.0  # 각 클립 4초 가정

        print(f"[VIDEO] Final video created: {output_path}")
        return {
            "video_path": str(output_path),
            "duration": duration,
            "resolution": "540x960"  # 9:16
        }

    except FileNotFoundError:
        print("[WARNING] FFmpeg not installed")
    except Exception as e:
        print(f"[ERROR] Composition failed: {e}")

    # 실패시 첫 번째 클립 반환
    return {
        "video_path": str(valid_clips[0]) if valid_clips else str(output_path),
        "duration": 4.0,
        "resolution": "540x960"
    }
