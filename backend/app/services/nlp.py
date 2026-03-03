# app/services/nlp.py
"""
NLP 서비스 - 텍스트 분석, 요약, 감정 분석, 가사 생성

실제 구현 시:
- Claude API 또는 GPT API 사용
- 감정 분석 모델 (BERT, RoBERTa 등)
"""
from typing import List, Dict, Any
import os

def summarize_and_emotion(story: str):
    """
    스토리 요약 및 감정 분석
    
    Args:
        story: 입력 스토리 텍스트
        
    Returns:
        tuple: (요약, 감정)
    """
    # TODO: Claude API 또는 GPT API로 실제 구현
    # from anthropic import Anthropic
    # client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    # response = client.messages.create(
    #     model="claude-3-5-sonnet-20241022",
    #     max_tokens=1024,
    #     messages=[{
    #         "role": "user",
    #         "content": f"다음 스토리를 3문장으로 요약하고 감정을 분석해주세요:\n\n{story}"
    #     }]
    # )
    
    # 임시 구현
    summary = story[:100] + "..." if len(story) > 100 else story
    
    # 간단한 감정 분석 (키워드 기반)
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
    """
    요약과 감정을 바탕으로 가사 생성
    
    Args:
        summary: 스토리 요약
        emotion: 감정 (happy, sad, angry, romantic, neutral)
        
    Returns:
        str: 생성된 가사
    """
    # TODO: Claude API로 실제 가사 생성
    # response = client.messages.create(
    #     model="claude-3-5-sonnet-20241022",
    #     max_tokens=2048,
    #     messages=[{
    #         "role": "user",
    #         "content": f"다음 스토리와 감정을 바탕으로 노래 가사를 작성해주세요:\n\n스토리: {summary}\n감정: {emotion}"
    #     }]
    # )
    
    # 임시 구현
    emotion_templates = {
        "happy": "밝은 햇살 아래\n우리의 이야기가 시작돼\n행복한 순간들\n영원히 기억할게",
        "sad": "눈물이 흐르는 밤\n그리운 기억들\n슬픈 멜로디에\n마음을 담아",
        "angry": "불타는 감정\n억눌린 외침\n이제는 말할게\n내 진심을",
        "romantic": "사랑하는 마음\n너에게 전하고 싶어\n영원한 약속\n함께 하자고",
        "neutral": "우리의 이야기\n담담하게 흘러가\n평온한 일상 속\n특별한 순간들"
    }
    
    lyrics = emotion_templates.get(emotion, emotion_templates["neutral"])
    lyrics = f"[Verse 1]\n{summary[:50]}...\n\n[Chorus]\n{lyrics}\n\n[Verse 2]\n계속되는 우리의 여정\n함께 만들어가는 이야기"

    return lyrics


def split_story_into_scenes(story: str, num_scenes: int = 5) -> List[Dict[str, Any]]:
    """
    스토리를 시각적 장면으로 분할

    Args:
        story: 전체 스토리 텍스트
        num_scenes: 생성할 장면 수 (기본 5개)

    Returns:
        list: 장면 설명 리스트 [{"index": 0, "description": "...", "prompt": "..."}]
    """
    # TODO: Claude API로 실제 장면 분할
    # response = client.messages.create(
    #     model="claude-3-5-sonnet-20241022",
    #     max_tokens=2048,
    #     messages=[{
    #         "role": "user",
    #         "content": f"""다음 스토리를 {num_scenes}개의 시각적 장면으로 나눠주세요.
    #         각 장면은 뮤직비디오의 한 컷으로 표현될 수 있어야 합니다.
    #
    #         스토리: {story}
    #
    #         JSON 형식으로 응답해주세요:
    #         [
    #             {{"index": 0, "description": "장면 설명", "prompt": "영어 이미지 프롬프트"}},
    #             ...
    #         ]"""
    #     }]
    # )

    # 임시 구현: 문장 단위로 분할
    sentences = []

    # 문장 분리 (마침표, 느낌표, 물음표 기준)
    import re
    raw_sentences = re.split(r'[.!?。！？]\s*', story)
    sentences = [s.strip() for s in raw_sentences if s.strip() and len(s.strip()) > 10]

    # 장면 수에 맞게 조절
    scenes = []
    if len(sentences) >= num_scenes:
        # 균등하게 선택
        step = len(sentences) // num_scenes
        for i in range(num_scenes):
            idx = min(i * step, len(sentences) - 1)
            scenes.append({
                "index": i,
                "description": sentences[idx],
                "prompt": None,
                "duration": 4.0
            })
    else:
        # 문장이 부족하면 스토리를 청크로 분할
        chunk_size = max(len(story) // num_scenes, 50)
        for i in range(num_scenes):
            start = i * chunk_size
            end = min(start + chunk_size, len(story))
            chunk = story[start:end].strip()
            if chunk:
                scenes.append({
                    "index": i,
                    "description": chunk,
                    "prompt": None,
                    "duration": 4.0
                })

    # 부족한 경우 기본 장면 추가
    while len(scenes) < num_scenes:
        scenes.append({
            "index": len(scenes),
            "description": f"Scene {len(scenes) + 1}",
            "prompt": None,
            "duration": 4.0
        })

    print(f"[NLP] Split story into {len(scenes)} scenes")
    return scenes[:num_scenes]


def generate_image_prompts(scenes: List[Dict], emotion: str, style: str = "cinematic") -> List[Dict]:
    """
    장면 설명을 이미지 생성 프롬프트로 변환

    Args:
        scenes: 장면 리스트
        emotion: 감정 (happy, sad, angry, romantic, neutral)
        style: 스타일 (cinematic, anime, realistic, etc.)

    Returns:
        list: 프롬프트가 추가된 장면 리스트
    """
    # 감정별 스타일 키워드
    emotion_styles = {
        "happy": "bright colors, warm lighting, cheerful atmosphere, golden hour, vibrant",
        "sad": "moody, blue tones, soft rain, melancholic, dim lighting, emotional",
        "angry": "intense red tones, dramatic shadows, stormy, powerful, dynamic",
        "romantic": "soft pink and purple hues, dreamy, bokeh, intimate, sunset",
        "neutral": "balanced colors, natural lighting, calm atmosphere, serene"
    }

    # 스타일별 키워드
    style_keywords = {
        "cinematic": "cinematic composition, film grain, movie still, professional photography, 4k",
        "anime": "anime style, vibrant colors, detailed illustration, studio ghibli inspired",
        "realistic": "photorealistic, hyperrealistic, DSLR photography, 85mm lens, sharp focus",
        "artistic": "oil painting style, impressionist, artistic, museum quality",
        "music_video": "music video aesthetic, dramatic lighting, stage lighting, concert style"
    }

    emotion_style = emotion_styles.get(emotion, emotion_styles["neutral"])
    style_kw = style_keywords.get(style, style_keywords["cinematic"])

    # 9:16 세로 비율 강조
    aspect_prompt = "vertical composition, portrait orientation, 9:16 aspect ratio"

    updated_scenes = []
    for scene in scenes:
        description = scene.get("description", "")

        # 영어로 변환 시도 (간단한 키워드 추가)
        # TODO: 실제로는 번역 API 사용
        prompt = f"{description}, {emotion_style}, {style_kw}, {aspect_prompt}, masterpiece, best quality"

        updated_scene = scene.copy()
        updated_scene["prompt"] = prompt
        updated_scenes.append(updated_scene)

    print(f"[NLP] Generated {len(updated_scenes)} image prompts")
    return updated_scenes


def analyze_story_full(story: str, num_scenes: int = 5) -> Dict[str, Any]:
    """
    스토리 전체 분석 (요약 + 감정 + 테마 + 장면 분할)

    Args:
        story: 스토리 텍스트
        num_scenes: 장면 수

    Returns:
        dict: 분석 결과
    """
    # 요약 및 감정 분석
    summary, emotion = summarize_and_emotion(story)

    # 테마 추출 (간단한 키워드 기반)
    theme = "general"
    if any(word in story.lower() for word in ["사랑", "love", "연인", "couple"]):
        theme = "love"
    elif any(word in story.lower() for word in ["모험", "adventure", "여행", "journey"]):
        theme = "adventure"
    elif any(word in story.lower() for word in ["성장", "growth", "꿈", "dream"]):
        theme = "growth"
    elif any(word in story.lower() for word in ["이별", "farewell", "추억", "memory"]):
        theme = "farewell"

    # 장면 분할
    scenes = split_story_into_scenes(story, num_scenes)

    # 장면에 프롬프트 추가
    scenes_with_prompts = generate_image_prompts(scenes, emotion)

    result = {
        "summary": summary,
        "emotion": emotion,
        "theme": theme,
        "scenes": scenes_with_prompts
    }

    print(f"[NLP] Story analysis complete: emotion={emotion}, theme={theme}, scenes={len(scenes)}")
    return result
