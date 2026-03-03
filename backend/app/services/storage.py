# app/services/storage.py
import os
from pathlib import Path

# 로컬 개발용: 파일 경로를 URL로 변환
def get_local_url(file_path, base_url: str = "http://localhost:8000"):
    """로컬 파일 경로를 서빙 가능한 URL로 변환"""
    if not file_path:
        return None

    path = Path(file_path)

    # outputs 폴더 기준 상대 경로 계산
    # ./outputs/samples/sample.mp3 -> samples/sample.mp3
    # ./outputs/image.png -> image.png
    try:
        # outputs 폴더를 기준으로 상대 경로 추출
        if "outputs" in str(path):
            parts = path.parts
            outputs_idx = parts.index("outputs")
            relative_parts = parts[outputs_idx + 1:]
            relative_path = "/".join(relative_parts)
            return f"{base_url}/files/{relative_path}"
    except (ValueError, IndexError):
        pass

    # 기본: 파일명만 사용
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
    # import uuid
    # s3 = boto3.client("s3")
    # BUCKET = "chanho-playground"
    # key = f"outputs/{uuid.uuid4()}/{Path(file_path).name}"
    # s3.upload_file(file_path, BUCKET, key)
    # return f"https://{BUCKET}.s3.amazonaws.com/{key}"

    # 개발용: 로컬 URL 반환
    return get_local_url(file_path)
