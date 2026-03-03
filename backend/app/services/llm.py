"""
로컬 LLM 서비스
GGUF 포맷의 모델을 로드하여 채팅 기능 제공
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Generator
from threading import Lock

# 모델 저장 경로 (파일 위치 기준 절대 경로)
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

# 모델 캐시 (싱글톤)
_model_cache: Dict[str, any] = {}
_model_lock = Lock()


def get_available_models() -> List[Dict[str, str]]:
    """사용 가능한 모델 목록 반환"""
    models = []

    if not MODELS_DIR.exists():
        return models

    for file in MODELS_DIR.glob("*.gguf"):
        models.append({
            "name": file.stem,
            "filename": file.name,
            "path": str(file),
            "size_mb": round(file.stat().st_size / (1024 * 1024), 2)
        })

    return models


def load_model(model_name: str):
    """모델 로드 (캐시 사용)"""
    try:
        from llama_cpp import Llama
    except ImportError:
        raise ImportError(
            "llama-cpp-python이 설치되지 않았습니다. "
            "pip install llama-cpp-python 으로 설치해주세요."
        )

    with _model_lock:
        if model_name in _model_cache:
            return _model_cache[model_name]

        # 모델 파일 찾기
        model_path = None
        for file in MODELS_DIR.glob("*.gguf"):
            if file.stem == model_name or file.name == model_name:
                model_path = file
                break

        if not model_path:
            raise FileNotFoundError(f"모델을 찾을 수 없습니다: {model_name}")

        print(f"🤖 모델 로딩 중: {model_path}")

        # GPU 레이어 설정 (환경 변수로 제어 가능)
        # 0: CPU만 사용, -1: 모든 레이어 GPU, 숫자: 해당 개수만 GPU
        n_gpu_layers = int(os.getenv("LLAMA_GPU_LAYERS", "0"))

        # 모델 로드
        try:
            model = Llama(
                model_path=str(model_path),
                n_ctx=4096,  # 컨텍스트 길이
                n_threads=os.cpu_count() or 4,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
        except Exception as e:
            print(f"⚠️ 모델 로드 실패 (GPU 설정 문제일 수 있음): {e}")
            print("🔄 CPU 전용 모드로 재시도...")
            # GPU 실패시 CPU로 재시도
            model = Llama(
                model_path=str(model_path),
                n_ctx=4096,
                n_threads=os.cpu_count() or 4,
                n_gpu_layers=0,  # CPU만 사용
                verbose=False
            )

        _model_cache[model_name] = model
        print(f"✅ 모델 로드 완료: {model_name}")

        return model


def unload_model(model_name: str) -> bool:
    """모델 언로드"""
    with _model_lock:
        if model_name in _model_cache:
            del _model_cache[model_name]
            return True
        return False


def chat_completion(
    model_name: str,
    messages: List[Dict[str, str]],
    max_tokens: int = 1024,
    temperature: float = 0.7,
    top_p: float = 0.9,
    stream: bool = False
) -> Generator[str, None, None] | str:
    """
    채팅 완성

    Parameters:
    - model_name: 모델 이름
    - messages: 대화 기록 [{"role": "user/assistant/system", "content": "..."}]
    - max_tokens: 최대 생성 토큰 수
    - temperature: 창의성 (0.0-2.0)
    - top_p: 핵 샘플링
    - stream: 스트리밍 여부
    """
    model = load_model(model_name)

    # 대화 형식 구성
    prompt = format_chat_prompt(messages)

    if stream:
        return _stream_completion(model, prompt, max_tokens, temperature, top_p)
    else:
        response = model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=["<|im_end|>", "<|endoftext|>", "</s>", "[/INST]"],
            echo=False
        )
        return response["choices"][0]["text"].strip()


def _stream_completion(
    model,
    prompt: str,
    max_tokens: int,
    temperature: float,
    top_p: float
) -> Generator[str, None, None]:
    """스트리밍 완성"""
    for output in model(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        stop=["<|im_end|>", "<|endoftext|>", "</s>", "[/INST]"],
        echo=False,
        stream=True
    ):
        token = output["choices"][0]["text"]
        yield token


def format_chat_prompt(messages: List[Dict[str, str]]) -> str:
    """
    대화 기록을 프롬프트 형식으로 변환
    ChatML 형식 사용 (많은 모델에서 지원)
    """
    prompt_parts = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            prompt_parts.append(f"<|im_start|>system\n{content}<|im_end|>")
        elif role == "user":
            prompt_parts.append(f"<|im_start|>user\n{content}<|im_end|>")
        elif role == "assistant":
            prompt_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")

    # 어시스턴트 응답 시작
    prompt_parts.append("<|im_start|>assistant\n")

    return "\n".join(prompt_parts)


def get_loaded_models() -> List[str]:
    """현재 로드된 모델 목록"""
    return list(_model_cache.keys())
