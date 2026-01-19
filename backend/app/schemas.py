from pydantic import BaseModel

class GenerateResponse(BaseModel):
    audio_url: str
    video_url: str
    emotion: str