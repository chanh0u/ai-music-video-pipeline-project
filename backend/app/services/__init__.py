# app/services/__init__.py
"""
AI 서비스 모듈

사용 가능한 서비스:
- nlp: 텍스트 분석, 요약, 감정 분석, 가사 생성
- music: AI 음악 생성
- video: 뮤직비디오 생성
- image: AI 이미지 생성
- storage: 파일 스토리지 관리
"""

from . import nlp, music, video, image, storage

__all__ = ['nlp', 'music', 'video', 'image', 'storage']
