# app/services/session.py
"""
세션 관리 서비스 - MV Wizard 세션 상태 관리

파일 기반 세션 저장소 (개발용, 추후 Redis 전환 가능)
"""
import json
import uuid
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# 세션 저장 디렉토리
SESSION_DIR = Path("./sessions")
SESSION_DIR.mkdir(exist_ok=True)

# 세션 만료 시간 (24시간)
SESSION_EXPIRY_HOURS = 24


def create_session() -> str:
    """
    새 세션 생성

    Returns:
        str: 생성된 세션 ID
    """
    session_id = str(uuid.uuid4())

    session_data = {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "current_step": 1,
        "story": None,
        "analysis": None,
        "lyrics": None,
        "music": None,
        "scenes": [],
        "images": [],
        "video_clips": [],
        "final_video": None,
        "youtube": None
    }

    session_path = SESSION_DIR / f"{session_id}.json"
    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    print(f"[SESSION] Created: {session_id}")
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    세션 조회

    Args:
        session_id: 세션 ID

    Returns:
        dict: 세션 데이터 (없으면 None)
    """
    session_path = SESSION_DIR / f"{session_id}.json"

    if not session_path.exists():
        print(f"[SESSION] Not found: {session_id}")
        return None

    with open(session_path, "r", encoding="utf-8") as f:
        session_data = json.load(f)

    # 만료 체크
    created_at = datetime.fromisoformat(session_data["created_at"])
    if datetime.now() - created_at > timedelta(hours=SESSION_EXPIRY_HOURS):
        print(f"[SESSION] Expired: {session_id}")
        delete_session(session_id)
        return None

    return session_data


def update_session(session_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    세션 업데이트

    Args:
        session_id: 세션 ID
        data: 업데이트할 데이터

    Returns:
        dict: 업데이트된 세션 데이터
    """
    session_data = get_session(session_id)
    if session_data is None:
        return None

    # 데이터 병합
    session_data.update(data)
    session_data["updated_at"] = datetime.now().isoformat()

    # 저장
    session_path = SESSION_DIR / f"{session_id}.json"
    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    print(f"[SESSION] Updated: {session_id}")
    return session_data


def delete_session(session_id: str) -> bool:
    """
    세션 삭제

    Args:
        session_id: 세션 ID

    Returns:
        bool: 삭제 성공 여부
    """
    session_path = SESSION_DIR / f"{session_id}.json"

    if session_path.exists():
        os.remove(session_path)
        print(f"[SESSION] Deleted: {session_id}")
        return True

    return False


def cleanup_expired_sessions():
    """만료된 세션 정리"""
    count = 0
    for session_file in SESSION_DIR.glob("*.json"):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            created_at = datetime.fromisoformat(session_data["created_at"])
            if datetime.now() - created_at > timedelta(hours=SESSION_EXPIRY_HOURS):
                os.remove(session_file)
                count += 1
        except Exception:
            pass

    if count > 0:
        print(f"[SESSION] Cleaned up {count} expired sessions")

    return count
