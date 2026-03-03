# app/routers/youtube.py
"""
YouTube API 라우터 - OAuth 인증 및 Shorts 업로드
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from typing import Optional

from app.schemas import YouTubeUploadRequest, YouTubeUploadResult
from app.services.youtube import youtube_service
from app.services import session as session_service

router = APIRouter()


@router.get("/status")
async def get_youtube_status():
    """
    YouTube API 설정 상태 확인

    Returns:
        dict: API 설정 상태
    """
    return {
        "service": "YouTube Data API v3",
        "is_configured": youtube_service.is_configured(),
        "features": {
            "oauth": "OAuth 2.0 인증",
            "upload": "YouTube Shorts 업로드"
        },
        "required_env": [
            "YOUTUBE_CLIENT_ID",
            "YOUTUBE_CLIENT_SECRET",
            "YOUTUBE_REDIRECT_URI"
        ]
    }


@router.get("/auth")
async def get_auth_url(session_id: str = Query(..., description="세션 ID")):
    """
    YouTube OAuth 인증 URL 생성

    Args:
        session_id: MV Wizard 세션 ID

    Returns:
        dict: 인증 URL
    """
    # 세션 확인
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    try:
        auth_url = youtube_service.get_auth_url(state=session_id)
        return {
            "auth_url": auth_url,
            "message": "YouTube 인증 페이지로 이동해주세요."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"인증 URL 생성 실패: {str(e)}")


@router.get("/callback")
async def oauth_callback(
    code: str = Query(None, description="OAuth 인증 코드"),
    state: str = Query(None, description="세션 ID"),
    error: str = Query(None, description="에러")
):
    """
    YouTube OAuth 콜백 처리

    인증 완료 후 프론트엔드로 리다이렉트

    Args:
        code: OAuth 인증 코드
        state: 세션 ID
        error: 에러 메시지 (인증 거부시)
    """
    if error:
        # 인증 거부 또는 에러
        return RedirectResponse(
            url=f"/mv-wizard.html?session_id={state}&youtube_error={error}",
            status_code=302
        )

    if not code:
        raise HTTPException(status_code=400, detail="인증 코드가 없습니다.")

    session_id = state
    if not session_id:
        raise HTTPException(status_code=400, detail="세션 ID가 없습니다.")

    try:
        # 토큰 교환
        result = youtube_service.exchange_code(code, session_id)

        # 성공시 프론트엔드로 리다이렉트
        return RedirectResponse(
            url=f"/mv-wizard.html?session_id={session_id}&youtube_auth=success",
            status_code=302
        )

    except ValueError as e:
        return RedirectResponse(
            url=f"/mv-wizard.html?session_id={session_id}&youtube_error={str(e)}",
            status_code=302
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/mv-wizard.html?session_id={session_id}&youtube_error=auth_failed",
            status_code=302
        )


@router.get("/auth-status/{session_id}")
async def check_auth_status(session_id: str):
    """
    YouTube 인증 상태 확인

    Args:
        session_id: 세션 ID

    Returns:
        dict: 인증 상태
    """
    status = youtube_service.check_auth_status(session_id)
    return status


@router.post("/upload/{session_id}")
async def upload_to_youtube(session_id: str, request: YouTubeUploadRequest):
    """
    YouTube Shorts 업로드

    Args:
        session_id: 세션 ID
        request: 업로드 요청 (제목, 설명, 태그, 공개설정)

    Returns:
        YouTubeUploadResult: 업로드 결과
    """
    # 세션 확인
    session_data = session_service.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    # 최종 비디오 확인
    final_video = session_data.get("final_video", {})
    video_path = final_video.get("video_path")

    if not video_path:
        raise HTTPException(status_code=400, detail="업로드할 비디오가 없습니다. 먼저 비디오를 생성해주세요.")

    try:
        # 업로드
        result = youtube_service.upload_shorts(
            session_id=session_id,
            video_path=video_path,
            title=request.title,
            description=request.description or "",
            tags=request.tags or [],
            privacy=request.privacy or "private"
        )

        # 세션 업데이트
        session_service.update_session(session_id, {
            "youtube": {
                "video_id": result["video_id"],
                "url": result["url"],
                "title": result["title"],
                "status": result["status"]
            }
        })

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"업로드 실패: {str(e)}")
