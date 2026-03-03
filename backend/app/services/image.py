# app/services/image.py
"""
Image 서비스 - AI 이미지 생성

지원하는 방법:
1. Replicate (Stable Diffusion) - 추천
2. Stability AI - 공식 API
3. OpenAI DALL-E
"""
from pathlib import Path
import uuid
import os

def generate_image_replicate(
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    num_outputs: int = 1
):
    """
    Replicate API로 이미지 생성 (Stable Diffusion)
    
    Args:
        prompt: 이미지 생성 프롬프트
        negative_prompt: 제외할 요소
        width: 이미지 너비
        height: 이미지 높이
        num_outputs: 생성할 이미지 개수
        
    Returns:
        list: 생성된 이미지 경로 리스트
    """
    try:
        import replicate
        
        print(f"[IMAGE] Replicate로 이미지 생성 중...")
        print(f"  - Prompt: {prompt}")
        print(f"  - Size: {width}x{height}")
        
        # Stable Diffusion 모델 실행
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
        
        # 결과 다운로드 및 저장
        image_paths = []
        import requests
        
        for i, image_url in enumerate(output):
            print(f"  - 다운로드 중: {i+1}/{len(output)}")
            
            # 이미지 다운로드
            response = requests.get(image_url)
            
            # 저장
            output_path = f"./outputs/image_{uuid.uuid4()}.png"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            image_paths.append(output_path)
            print(f"  ✓ 저장 완료: {output_path}")
        
        return image_paths
        
    except ImportError:
        print("[ERROR] replicate 패키지가 설치되지 않았습니다.")
        print("설치: pip install replicate")
        raise
    except Exception as e:
        print(f"[ERROR] Replicate 이미지 생성 실패: {str(e)}")
        raise


def generate_image_stability(
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    style_preset: str = None
):
    """
    Stability AI 공식 API로 이미지 생성
    
    Args:
        prompt: 이미지 생성 프롬프트
        negative_prompt: 제외할 요소
        width: 이미지 너비 (64의 배수)
        height: 이미지 높이 (64의 배수)
        style_preset: 스타일 (anime, digital-art, photographic 등)
        
    Returns:
        str: 생성된 이미지 경로
    """
    try:
        import requests
        import base64
        
        api_key = os.getenv("STABILITY_API_KEY")
        if not api_key:
            raise ValueError("STABILITY_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        print(f"[IMAGE] Stability AI로 이미지 생성 중...")
        
        # API 요청
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1
                    },
                    {
                        "text": negative_prompt,
                        "weight": -1
                    }
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
        
        # 이미지 저장
        data = response.json()
        
        output_path = f"./outputs/image_{uuid.uuid4()}.png"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(data["artifacts"][0]["base64"]))
        
        print(f"  ✓ 저장 완료: {output_path}")
        
        return [output_path]
        
    except Exception as e:
        print(f"[ERROR] Stability AI 이미지 생성 실패: {str(e)}")
        raise


def generate_image_dalle(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    n: int = 1
):
    """
    OpenAI DALL-E로 이미지 생성
    
    Args:
        prompt: 이미지 생성 프롬프트
        size: 이미지 크기 (1024x1024, 1792x1024, 1024x1792)
        quality: 품질 (standard, hd)
        n: 생성할 이미지 개수
        
    Returns:
        list: 생성된 이미지 경로 리스트
    """
    try:
        from openai import OpenAI
        import requests
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        client = OpenAI(api_key=api_key)
        
        print(f"[IMAGE] DALL-E로 이미지 생성 중...")
        
        # 이미지 생성
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
        )
        
        # 이미지 다운로드 및 저장
        image_paths = []
        
        for i, image_data in enumerate(response.data):
            print(f"  - 다운로드 중: {i+1}/{len(response.data)}")
            
            # 이미지 다운로드
            image_response = requests.get(image_data.url)
            
            # 저장
            output_path = f"./outputs/image_{uuid.uuid4()}.png"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "wb") as f:
                f.write(image_response.content)
            
            image_paths.append(output_path)
            print(f"  ✓ 저장 완료: {output_path}")
        
        return image_paths
        
    except Exception as e:
        print(f"[ERROR] DALL-E 이미지 생성 실패: {str(e)}")
        raise


def generate_image(
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    num_outputs: int = 1,
    provider: str = "replicate"
):
    """
    이미지 생성 (여러 제공자 지원)
    
    Args:
        prompt: 이미지 생성 프롬프트
        negative_prompt: 제외할 요소
        width: 이미지 너비
        height: 이미지 높이
        num_outputs: 생성할 이미지 개수
        provider: AI 제공자 (replicate, stability, dalle)
        
    Returns:
        list: 생성된 이미지 경로 리스트
    """
    # 임시 구현 (API 키 없을 때)
    if os.getenv("REPLICATE_API_TOKEN") is None and provider == "replicate":
        print("[WARNING] REPLICATE_API_TOKEN이 설정되지 않았습니다.")
        print("임시 경로를 반환합니다.")
        
        output_path = f"./outputs/image_{uuid.uuid4()}.png"
        print(f"[IMAGE] 이미지 생성 요청:")
        print(f"  - Prompt: {prompt}")
        print(f"  - Negative: {negative_prompt}")
        print(f"  - Size: {width}x{height}")
        print(f"  - Count: {num_outputs}")
        print(f"  - Output: {output_path}")
        
        return [output_path]
    
    # 실제 구현
    if provider == "replicate":
        return generate_image_replicate(prompt, negative_prompt, width, height, num_outputs)
    elif provider == "stability":
        return generate_image_stability(prompt, negative_prompt, width, height)
    elif provider == "dalle":
        size = f"{width}x{height}"
        return generate_image_dalle(prompt, size, n=num_outputs)
    else:
        raise ValueError(f"지원하지 않는 제공자: {provider}")


def enhance_prompt(prompt: str):
    """
    프롬프트 개선 (선택사항)

    Claude나 GPT로 프롬프트를 더 상세하고 효과적으로 만듭니다.

    Args:
        prompt: 원본 프롬프트

    Returns:
        str: 개선된 프롬프트
    """
    # TODO: Claude API로 프롬프트 개선
    # from anthropic import Anthropic
    # client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    # response = client.messages.create(
    #     model="claude-3-5-sonnet-20241022",
    #     max_tokens=1024,
    #     messages=[{
    #         "role": "user",
    #         "content": f"""다음 이미지 생성 프롬프트를 Stable Diffusion에 최적화된
    #         상세한 프롬프트로 개선해주세요. 영어로 작성하고, 구체적인 스타일, 조명,
    #         구도 등을 포함해주세요:
    #
    #         {prompt}"""
    #     }]
    # )
    # enhanced = response.content[0].text

    # 임시: 기본 개선
    if prompt and not any(word in prompt.lower() for word in ["detailed", "high quality", "masterpiece"]):
        enhanced = f"{prompt}, highly detailed, masterpiece, best quality, 8k"
    else:
        enhanced = prompt

    return enhanced


# ========== MV Wizard 용 9:16 이미지 생성 ==========

def generate_shorts_image(
    prompt: str,
    style: str = "cinematic",
    provider: str = "replicate",
    session_id: str = None,
    scene_index: int = 0
):
    """
    YouTube Shorts용 9:16 세로 이미지 생성

    Args:
        prompt: 이미지 생성 프롬프트
        style: 스타일 (cinematic, anime, realistic, etc.)
        provider: AI 제공자 (replicate, stability, dalle)
        session_id: 세션 ID (파일명용)
        scene_index: 장면 인덱스

    Returns:
        str: 생성된 이미지 경로
    """
    # 9:16 비율 사이즈 (Shorts/TikTok/Reels)
    # SDXL 권장 사이즈: 768x1344 (9:16에 가까움)
    width = 768
    height = 1344

    # 스타일별 프롬프트 보강
    style_prompts = {
        "cinematic": "cinematic lighting, film grain, movie still, professional, 4k",
        "anime": "anime style, vibrant colors, detailed illustration, studio quality",
        "realistic": "photorealistic, DSLR photography, 85mm lens, sharp focus",
        "artistic": "digital art, artistic, trending on artstation",
        "music_video": "music video aesthetic, dramatic lighting, concert atmosphere"
    }

    style_suffix = style_prompts.get(style, style_prompts["cinematic"])

    # 프롬프트 조합
    full_prompt = f"{prompt}, {style_suffix}, vertical composition, portrait orientation"

    # 네거티브 프롬프트
    negative_prompt = "blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, text"

    print(f"[IMAGE] Generating 9:16 image for scene {scene_index}")
    print(f"  - Size: {width}x{height}")
    print(f"  - Style: {style}")

    # API 키 확인
    api_key = os.getenv("REPLICATE_API_TOKEN")

    if api_key and provider == "replicate":
        # 실제 이미지 생성
        try:
            result = generate_image_replicate(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_outputs=1
            )
            return result[0] if result else None
        except Exception as e:
            print(f"[ERROR] Image generation failed: {e}")
            # 실패시 플레이스홀더 생성
            return create_placeholder_image(session_id, scene_index)
    else:
        # 개발 모드: 플레이스홀더 이미지 생성
        return create_placeholder_image(session_id, scene_index)


def create_placeholder_image(session_id: str = None, scene_index: int = 0):
    """
    개발용 플레이스홀더 이미지 생성 (Pillow 사용)

    Args:
        session_id: 세션 ID
        scene_index: 장면 인덱스

    Returns:
        str: 생성된 이미지 경로
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[WARNING] Pillow not installed. Returning mock path.")
        output_path = f"./outputs/scene_{scene_index}_{uuid.uuid4()}.png"
        return output_path

    # 9:16 사이즈 (작은 버전)
    width, height = 540, 960

    # 장면별 색상 팔레트
    colors = [
        (102, 126, 234),   # 파랑
        (118, 75, 162),    # 보라
        (240, 147, 43),    # 주황
        (46, 204, 113),    # 초록
        (231, 76, 60),     # 빨강
    ]

    bg_color = colors[scene_index % len(colors)]

    # 이미지 생성
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 장면 번호 텍스트
    text = f"Scene {scene_index + 1}"

    # 폰트 (시스템 기본)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()

    # 텍스트 위치 계산 (중앙)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # 텍스트 그리기
    draw.text((x, y), text, fill=(255, 255, 255), font=font)

    # 저장
    output_dir = Path("./outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"scene_{scene_index}_{session_id[:8] if session_id else uuid.uuid4()}.png"
    output_path = output_dir / filename

    img.save(output_path)
    print(f"[IMAGE] Placeholder created: {output_path}")

    return str(output_path)


def generate_scene_images(
    scenes: list,
    style: str = "cinematic",
    session_id: str = None
) -> list:
    """
    여러 장면의 이미지 일괄 생성

    Args:
        scenes: 장면 리스트 [{"index": 0, "prompt": "..."}]
        style: 스타일
        session_id: 세션 ID

    Returns:
        list: 생성된 이미지 정보 리스트
    """
    results = []

    for scene in scenes:
        index = scene.get("index", len(results))
        prompt = scene.get("prompt", scene.get("description", f"Scene {index + 1}"))

        image_path = generate_shorts_image(
            prompt=prompt,
            style=style,
            session_id=session_id,
            scene_index=index
        )

        results.append({
            "index": index,
            "image_path": image_path,
            "prompt": prompt
        })

    print(f"[IMAGE] Generated {len(results)} scene images")
    return results
