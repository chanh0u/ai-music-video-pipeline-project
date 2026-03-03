from fastapi import APIRouter, UploadFile, File

router = APIRouter()


@router.post("/convert")
async def convert_to_3d(file: UploadFile = File(...)):
    """2D 이미지를 3D 모델로 변환"""
    return {
        "status": "coming_soon",
        "message": "2D to 3D 변환 기능은 현재 개발 중입니다.",
    }


@router.get("/status")
async def get_status():
    """서비스 상태 확인"""
    return {
        "service": "2D to 3D Conversion",
        "status": "coming_soon",
    }
