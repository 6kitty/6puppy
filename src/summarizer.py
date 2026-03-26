"""
Claude Haiku를 이용한 블로그 포스트 요약 모듈
아침별점 스타일로 따뜻하게 요약
"""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SUMMARY_SYSTEM_PROMPT = """당신은 아침 운세 방송 진행자처럼 따뜻하고 가볍게 말하는 조수입니다.
블로그 글을 읽고, 아침별점 운세 풀이 스타일로 2~3문장 요약을 작성하세요.

규칙:
- 핵심 내용을 담되, 운세 조언하듯 부드럽고 따뜻한 말투로
- 마치 "이번 주 배운 것들이 큰 성장의 씨앗이 되는 날이에요" 같은 느낌
- 너무 딱딱한 기술 요약이 아닌, 읽고 싶어지는 한 줄 요약
- 2~3문장, 간결하게
- 한국어로 작성"""

async def summarize_post(title: str, content: str, author: str = "작성자") -> str:
    """
    블로그 포스트를 아침별점 스타일로 요약

    Args:
        title: 포스트 제목
        content: 포스트 내용 (마크다운)
        author: 작성자 이름

    Returns:
        요약 문자열
    """
    # 너무 긴 내용은 앞부분만 사용 (토큰 절약)
    max_content_length = 3000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "\n\n[이하 생략...]"

    user_prompt = f"""다음 블로그 포스트를 요약해주세요.

제목: {title}
작성자: {author}

내용:
{content}

위 글을 아침별점 스타일로 2~3문장으로 요약해주세요."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=SUMMARY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f"[summarizer] Claude API 오류: {e}")
        return "이번 글도 소중한 기록이 되었어요 ✨"
