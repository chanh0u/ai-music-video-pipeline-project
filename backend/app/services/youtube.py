# app/services/youtube.py
"""
YouTube 서비스 - OAuth 인증 및 Shorts 업로드

사용 전 Google Cloud Console에서:
1. YouTube Data API v3 활성화
2. OAuth 2.0 클라이언트 ID 생성
3. 환경 변수 설정:
   - YOUTUBE_CLIENT_ID
   - YOUTUBE_CLIENT_SECRET
   - YOUTUBE_REDIRECT_URI
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

# 토큰 저장 디렉토리
TOKEN_DIR = Path("./tokens")
TOKEN_DIR.mkdir(exist_ok=True)


class YouTubeService:
    """YouTube API 서비스"""

    def __init__(self):
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/api/youtube/callback")

        # OAuth 스코프
        self.scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly"
        ]

    def is_configured(self) -> bool:
        """YouTube API 설정 여부 확인"""
        return bool(self.client_id and self.client_secret)

    def get_auth_url(self, state: str = None) -> str:
        """
        OAuth 인증 URL 생성

        Args:
            state: 상태 값 (세션 ID 등)

        Returns:
            str: OAuth 인증 URL
        """
        if not self.is_configured():
            raise ValueError("YouTube API가 설정되지 않았습니다. 환경 변수를 확인해주세요.")

        try:
            from google_auth_oauthlib.flow import Flow

            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri

            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                state=state or ""
            )

            return auth_url

        except ImportError:
            print("[ERROR] google-auth-oauthlib not installed")
            raise ValueError("YouTube 인증에 필요한 패키지가 설치되지 않았습니다.")

    def exchange_code(self, code: str, session_id: str = None) -> Dict[str, Any]:
        """
        인증 코드를 액세스 토큰으로 교환

        Args:
            code: OAuth 인증 코드
            session_id: 세션 ID (토큰 저장용)

        Returns:
            dict: 토큰 정보
        """
        if not self.is_configured():
            raise ValueError("YouTube API가 설정되지 않았습니다.")

        try:
            from google_auth_oauthlib.flow import Flow

            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri

            # 코드 교환
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # 토큰 저장
            token_data = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": list(credentials.scopes)
            }

            if session_id:
                token_path = TOKEN_DIR / f"{session_id}_youtube.json"
                with open(token_path, "w") as f:
                    json.dump(token_data, f)
                print(f"[YOUTUBE] Token saved: {token_path}")

            return {
                "success": True,
                "message": "YouTube 인증 완료"
            }

        except Exception as e:
            print(f"[ERROR] Token exchange failed: {e}")
            raise ValueError(f"토큰 교환 실패: {str(e)}")

    def get_credentials(self, session_id: str):
        """
        저장된 인증 정보 로드

        Args:
            session_id: 세션 ID

        Returns:
            google.oauth2.credentials.Credentials
        """
        token_path = TOKEN_DIR / f"{session_id}_youtube.json"

        if not token_path.exists():
            return None

        try:
            from google.oauth2.credentials import Credentials

            with open(token_path, "r") as f:
                token_data = json.load(f)

            credentials = Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri"),
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=token_data.get("scopes")
            )

            return credentials

        except Exception as e:
            print(f"[ERROR] Failed to load credentials: {e}")
            return None

    def upload_shorts(
        self,
        session_id: str,
        video_path: str,
        title: str,
        description: str = "",
        tags: list = None,
        privacy: str = "private"
    ) -> Dict[str, Any]:
        """
        YouTube Shorts 업로드

        Args:
            session_id: 세션 ID (인증 정보 조회용)
            video_path: 비디오 파일 경로
            title: 비디오 제목
            description: 비디오 설명
            tags: 태그 리스트
            privacy: 공개 설정 (private, unlisted, public)

        Returns:
            dict: 업로드 결과 {video_id, url, status}
        """
        credentials = self.get_credentials(session_id)
        if not credentials:
            raise ValueError("YouTube 인증이 필요합니다.")

        if not Path(video_path).exists():
            raise ValueError("비디오 파일을 찾을 수 없습니다.")

        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            # YouTube API 클라이언트 생성
            youtube = build("youtube", "v3", credentials=credentials)

            # 비디오 메타데이터
            body = {
                "snippet": {
                    "title": title[:100],  # 최대 100자
                    "description": description[:5000] if description else "",  # 최대 5000자
                    "tags": tags[:500] if tags else [],  # 최대 500개
                    "categoryId": "10"  # Music 카테고리
                },
                "status": {
                    "privacyStatus": privacy,
                    "selfDeclaredMadeForKids": False
                }
            }

            # Shorts 인식을 위해 제목에 #Shorts 추가
            if "#Shorts" not in title and "#shorts" not in title:
                body["snippet"]["title"] = f"{title[:90]} #Shorts"

            # 업로드
            media = MediaFileUpload(
                video_path,
                mimetype="video/mp4",
                resumable=True
            )

            print(f"[YOUTUBE] Uploading: {title}")

            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"[YOUTUBE] Upload progress: {int(status.progress() * 100)}%")

            video_id = response.get("id")
            video_url = f"https://www.youtube.com/shorts/{video_id}"

            print(f"[YOUTUBE] Upload complete: {video_url}")

            return {
                "video_id": video_id,
                "url": video_url,
                "title": body["snippet"]["title"],
                "status": privacy
            }

        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            raise ValueError(f"업로드 실패: {str(e)}")

    def check_auth_status(self, session_id: str) -> Dict[str, Any]:
        """
        인증 상태 확인

        Args:
            session_id: 세션 ID

        Returns:
            dict: 인증 상태
        """
        credentials = self.get_credentials(session_id)

        return {
            "is_authenticated": credentials is not None,
            "is_configured": self.is_configured()
        }


# 싱글톤 인스턴스
youtube_service = YouTubeService()
