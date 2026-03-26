"""
육키티조수육퍼피 - 메인 진입점
Discord 봇 + FastAPI Webhook 서버를 동시에 실행
"""

import os
import asyncio
import threading
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from src.bot import bot
from src.webhook_server import app as webhook_app, set_discord_bot


def run_webhook_server():
    """별도 스레드에서 FastAPI webhook 서버 실행"""
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("WEBHOOK_PORT", "8080"))
    uvicorn.run(webhook_app, host=host, port=port, log_level="info")


async def main():
    # Discord 봇이 ready 상태가 된 후 webhook 서버에 주입
    @bot.event
    async def on_ready_inject():
        set_discord_bot(bot)

    # Webhook 서버를 별도 스레드에서 실행
    webhook_thread = threading.Thread(target=run_webhook_server, daemon=True)
    webhook_thread.start()
    print(f"[main] Webhook 서버 시작: {os.getenv('WEBHOOK_HOST', '0.0.0.0')}:{os.getenv('WEBHOOK_PORT', '8080')}")

    # Discord 봇 실행
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN이 설정되지 않았습니다. .env 파일을 확인하세요.")

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
