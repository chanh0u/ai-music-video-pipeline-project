# services/nlp.py

import os
import requests

HF_TOKEN = "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"

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN 환경변수가 없습니다")

# HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct"
HF_API_URL = "https://router.huggingface.co/api-inference/mistralai/Mistral-7B-Instruct"
HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}
def analyze_story(story: str):
    prompt = f"""다음 줄거리를 요약하고 주요 감정을 하나로 말해줘.
            줄거리:
            {story}
            형식:
            요약: ...
            감정: ...
            """
    response = requests.post(
        HF_API_URL,
        headers=HEADERS,
        json={
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.7
            }
        }
    )

    result = response.json()

    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError(result["error"])

    text = result[0]["generated_text"]

    return text, "emotional"


def generate_lyrics(summary: str, emotion: str):
    prompt = f"""감정: {emotion}
    줄거리 요약: {summary}
    위 내용을 바탕으로
    30초 분량의 노래 가사를 만들어줘.
    """

    response = requests.post(
        HF_API_URL,
        headers=HEADERS,
        json={
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.9
            }
        }
    )

    result = response.json()

    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError(result["error"])

    return result[0]["generated_text"]

