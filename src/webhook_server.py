"""
GitHub Webhook 수신 서버 (FastAPI)
push 이벤트에서 _posts 디렉토리 변경 감지
"""

import os
import hmac
import hashlib
import asyncio
import discord
from fastapi import FastAPI, Request, HTTPException, Header
from dotenv import load_dotenv

from .github_client import get_post_content, build_post_url
from .summarizer import summarize_post
from .message_builder import build_post_notification
from .config_manager import get_user_by_repo

load_dotenv()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()

app = FastAPI(title="육키티조수육퍼피 Webhook Server")

# Discord 봇 인스턴스는 main.py에서 주입됨
_discord_bot: discord.Client = None

def set_discord_bot(bot: discord.Client):
    global _discord_bot
    _discord_bot = bot


def _verify_signature(payload: bytes, signature: str) -> bool:
    """GitHub Webhook 서명 검증"""
    if not WEBHOOK_SECRET:
        return True  # 개발환경에서 시크릿 없으면 스킵

    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET, payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None)
):
    """GitHub Webhook 수신 엔드포인트"""
    payload_bytes = await request.body()

    # 서명 검증
    if not _verify_signature(payload_bytes, x_hub_signature_256 or ""):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # push 이벤트만 처리
    if x_github_event != "push":
        return {"status": "ignored", "event": x_github_event}

    payload = await request.json()

    # 레포 정보
    repo_full_name = payload.get("repository", {}).get("full_name", "")
    ref = payload.get("ref", "")

    # main 브랜치 push만 처리
    if ref not in ("refs/heads/main", "refs/heads/master"):
        return {"status": "ignored", "reason": "not main branch"}

    # _posts에 추가된 파일 찾기
    added_posts = []
    for commit in payload.get("commits", []):
        for file_path in commit.get("added", []) + commit.get("modified", []):
            if "_posts/" in file_path and file_path.endswith(".md"):
                added_posts.append(file_path)

    if not added_posts:
        return {"status": "ignored", "reason": "no new posts"}

    # 등록된 유저 찾기
    user_config = get_user_by_repo(repo_full_name)
    if not user_config:
        print(f"[webhook] 등록되지 않은 레포: {repo_full_name}")
        return {"status": "ignored", "reason": "repo not registered"}

    # 비동기로 Discord 메시지 전송
    asyncio.create_task(_process_new_posts(added_posts, user_config, repo_full_name))

    return {"status": "processing", "posts": added_posts}


async def _process_new_posts(file_paths: list, user_config: dict, repo: str):
    """새 포스트 처리 및 Discord 알림 전송"""
    if not _discord_bot:
        print("[webhook] Discord 봇이 연결되지 않았습니다")
        return

    channel_id = int(user_config.get("discord_channel_id") or os.getenv("DISCORD_CHANNEL_ID"))
    channel = _discord_bot.get_channel(channel_id)

    if not channel:
        print(f"[webhook] 채널을 찾을 수 없음: {channel_id}")
        return

    for file_path in file_paths:
        try:
            # 포스트 내용 가져오기
            title, content = await get_post_content(repo, file_path)

            # URL 생성
            repo_name = repo.split("/")[1]
            author = user_config.get("github_username", "작성자")
            url = build_post_url(author, repo_name, file_path)

            # Claude로 요약
            summary = await summarize_post(title, content, author)

            # Discord Embed 메시지 생성 및 전송
            embed = build_post_notification(
                author=user_config.get("id", author),
                title=title,
                url=url,
                summary=summary
            )

            await channel.send(embed=embed)
            print(f"[webhook] 알림 전송 완료: {title}")

        except Exception as e:
            print(f"[webhook] 포스트 처리 오류 ({file_path}): {e}")


@app.get("/health")
async def health_check():
    return {"status": "ok", "bot_connected": _discord_bot is not None}
