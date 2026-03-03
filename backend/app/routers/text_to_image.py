from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services import image
from app.services.storage import upload_s3

router = APIRouter()


class TextToImageResponse(BaseModel):
    """이미지 생성 응답"""
    status: str
    prompt: str
    enhanced_prompt: Optional[str] = None
    image_urls: List[str]
    count: int


@router.post("/generate", response_model=TextToImageResponse)
async def generate_image_endpoint(
    prompt: str = Form(...),
    negative_prompt: str = Form(""),
    width: int = Form(512),
    height: int = Form(512),
    num_outputs: int = Form(1),
    provider: str = Form("replicate"),
    enhance: bool = Form(False)
):
    """
    텍스트로 이미지 생성
    
    Parameters:
    - prompt: 이미지 설명
    - negative_prompt: 제외할 요소
    - width: 너비 (64의 배수)
    - height: 높이 (64의 배수)  
    - num_outputs: 생성 개수 (1-4)
    - provider: replicate/stability/dalle
    - enhance: 프롬프트 개선
    """
    
    try:
        print("\n🎨 Text to Image Generation Started")
        
        # 입력 검증
        if num_outputs < 1 or num_outputs > 4:
            raise HTTPException(status_code=400, detail="num_outputs는 1-4 사이여야 합니다.")
        
        if width % 64 != 0 or height % 64 != 0:
            raise HTTPException(status_code=400, detail="width와 height는 64의 배수여야 합니다.")
        
        # 프롬프트 개선
        enhanced_prompt = None
        if enhance:
            enhanced_prompt = image.enhance_prompt(prompt)
            final_prompt = enhanced_prompt
        else:
            final_prompt = prompt
        
        # 이미지 생성
        image_paths = image.generate_image(
            prompt=final_prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_outputs=num_outputs,
            provider=provider
        )
        
        # URL 생성
        image_urls = [upload_s3(path) for path in image_paths]
        
        return TextToImageResponse(
            status="success",
            prompt=prompt,
            enhanced_prompt=enhanced_prompt,
            image_urls=image_urls,
            count=len(image_urls)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """서비스 상태 확인"""
    import os
    
    return {
        "service": "Text to Image",
        "status": "operational",
        "providers": {
            "replicate": os.getenv("REPLICATE_API_TOKEN") is not None,
            "stability": os.getenv("STABILITY_API_KEY") is not None,
            "dalle": os.getenv("OPENAI_API_KEY") is not None
        }
    }
