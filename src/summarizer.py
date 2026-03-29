"""
Gemini 기반 블로그 포스트 요약 모듈 (단일 파일 버전)
- API Key Rotation 포함
- Rate Limit 자동 회피
"""

from __future__ import annotations

import os
import time
import logging
from itertools import cycle
from threading import Lock
from typing import Optional

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# 🔥 Gemini Key Pool
# ─────────────────────────────────────────

def _load_keys() -> list[str]:
    keys = []
    i = 1
    while True:
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if not key:
            break
        keys.append(key)
        i += 1

    if not keys:
        raise ValueError("GEMINI_API_KEY_1 이상 환경변수 필요")

    logger.info(f"Gemini Key Pool: {len(keys)}개 로드됨")
    return keys


class GeminiKeyPool:
    def __init__(self, model_name: str = "gemini-2.0-flash-lite"):
        self._keys = _load_keys()
        self._pool = cycle(self._keys)
        self._lock = Lock()
        self._current = next(self._pool)
        self._exhausted: set[str] = set()
        self._model_name = model_name

    def _next_key(self) -> Optional[str]:
        with self._lock:
            tried = 0
            while tried < len(self._keys):
                key = next(self._pool)
                if key not in self._exhausted:
                    self._current = key
                    return key
                tried += 1
            return None

    def generate(self, prompt: str, max_retries: int = None) -> str:
        if max_retries is None:
            max_retries = len(self._keys)

        last_error = None

        for _ in range(max_retries):
            current_key = self._current

            try:
                genai.configure(api_key=current_key)
                response = genai.generate_text(
                    model=self._model_name,
                    prompt=prompt,
                    temperature=0.2,
                    max_output_tokens=512,
                )
                print("[DEBUG] Gemini raw response:", response)
                if hasattr(response, "text") and response.text:
                    return response.text.strip()

                # fallback for older response shapes
                try:
                    return response.candidates[0].content.parts[0].text.strip()
                except Exception:
                    return "이번 글도 소중한 기록이 되었어요 ✨"

            except Exception as e:
                err = str(e)

                # 🔥 Rate limit 대응
                if any(x in err for x in ["429", "RESOURCE_EXHAUSTED", "quota", "rate limit"]):
                    logger.warning("Rate limit → 다음 키로 교체")

                    self._exhausted.add(current_key)
                    next_key = self._next_key()

                    if next_key is None:
                        logger.error("모든 키 소진 → 60초 대기")
                        self._exhausted.clear()
                        time.sleep(60)
                        self._next_key()

                    time.sleep(1)
                    last_error = e
                else:
                    raise

        raise Exception(f"모든 재시도 실패: {last_error}")


# 🔥 전역 싱글톤
_pool: Optional[GeminiKeyPool] = None

def get_pool() -> GeminiKeyPool:
    global _pool
    if _pool is None:
        _pool = GeminiKeyPool()
    return _pool


# ─────────────────────────────────────────
# 🔥 Summarizer
# ─────────────────────────────────────────

SUMMARY_SYSTEM_PROMPT = """당신은 아침 운세 방송 진행자처럼 따뜻하고 가볍게 말하는 조수입니다.
블로그 글을 읽고, 아침별점 운세 풀이 스타일로 2~3문장 요약을 작성하세요.

규칙:
- 핵심 내용을 담되, 운세 조언하듯 부드럽고 따뜻한 말투로
- 마치 "이번 주 배운 것들이 큰 성장의 씨앗이 되는 날이에요" 같은 느낌
- 너무 딱딱한 기술 요약이 아닌, 읽고 싶어지는 한 줄 요약
- 2~3문장, 간결하게
- 한국어로 작성"""


async def summarize_post(title: str, content: str, author: str = "작성자") -> str:
    max_content_length = 3000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "\n\n[이하 생략...]"

    prompt = f"""{SUMMARY_SYSTEM_PROMPT}

다음 블로그 포스트를 요약해주세요.

제목: {title}
작성자: {author}

내용:
{content}

요약:"""

    try:
        pool = get_pool()
        result = pool.generate(prompt)

        if not result or not result.strip():
            return "이번 글도 소중한 기록이 되었어요 ✨"

        return result.strip()

    except Exception as e:
        print(f"[summarizer] Gemini API 오류: {e}")
        return "이번 글도 소중한 기록이 되었어요 ✨"