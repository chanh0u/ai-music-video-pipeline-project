"""
로컬 LLM 채팅 API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json

from app.services import llm

router = APIRouter()


class Message(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    model: str
    message: Message
    usage: Optional[dict] = None


class ModelInfo(BaseModel):
    name: str
    filename: str
    path: str
    size_mb: float


@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """사용 가능한 모델 목록 조회"""
    models = llm.get_available_models()
    return models


@router.get("/models/loaded")
async def list_loaded_models():
    """현재 메모리에 로드된 모델 목록"""
    return {"loaded_models": llm.get_loaded_models()}


@router.post("/models/{model_name}/load")
async def load_model(model_name: str):
    """모델을 메모리에 로드"""
    try:
        llm.load_model(model_name)
        return {"status": "success", "message": f"모델 '{model_name}' 로드 완료"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"모델 로드 실패: {str(e)}")


@router.post("/models/{model_name}/unload")
async def unload_model(model_name: str):
    """모델을 메모리에서 언로드"""
    if llm.unload_model(model_name):
        return {"status": "success", "message": f"모델 '{model_name}' 언로드 완료"}
    else:
        raise HTTPException(status_code=404, detail=f"로드된 모델이 없습니다: {model_name}")


@router.post("/chat")
async def chat_completion(request: ChatRequest):
    """채팅 완성 API"""
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        if request.stream:
            # 스트리밍 응답
            async def generate():
                try:
                    for token in llm.chat_completion(
                        model_name=request.model,
                        messages=messages,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        stream=True
                    ):
                        # SSE 형식
                        data = json.dumps({"token": token}, ensure_ascii=False)
                        yield f"data: {data}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
                    yield f"data: {error_data}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # 일반 응답
            response_text = llm.chat_completion(
                model_name=request.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stream=False
            )

            return ChatResponse(
                model=request.model,
                message=Message(role="assistant", content=response_text)
            )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 생성 실패: {str(e)}")


@router.get("/status")
async def get_status():
    """서비스 상태 확인"""
    llama_installed = False
    llama_version = None
    cuda_available = False

    try:
        import llama_cpp
        llama_installed = True
        llama_version = getattr(llama_cpp, "__version__", "unknown")

        # CUDA 지원 확인
        try:
            # llama_cpp가 CUDA로 빌드되었는지 확인
            cuda_available = hasattr(llama_cpp, 'llama_backend_init')
        except:
            pass
    except ImportError:
        pass

    models = llm.get_available_models()
    models_dir = str(llm.MODELS_DIR)

    return {
        "service": "Local LLM Chat",
        "status": "operational" if llama_installed else "llama-cpp-python 설치 필요",
        "llama_cpp_installed": llama_installed,
        "llama_cpp_version": llama_version,
        "cuda_available": cuda_available,
        "models_directory": models_dir,
        "available_models": len(models),
        "model_list": [m["name"] for m in models],
        "loaded_models": llm.get_loaded_models(),
        "help": {
            "install": "pip install llama-cpp-python",
            "install_cuda": "pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121",
            "gpu_env": "LLAMA_GPU_LAYERS=0 (CPU) 또는 -1 (전체 GPU)"
        }
    }
