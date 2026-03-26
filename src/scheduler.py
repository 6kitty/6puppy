"""
주간 스케줄러
매주 일요일 KST 20:00 - 회고 미작성 시 재촉 메시지 전송
"""

import os
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from .config_manager import get_all_users
from .github_client import has_post_this_week
from .message_builder import build_reminder_message

KST = pytz.timezone("Asia/Seoul")


def setup_scheduler(bot: discord.Client) -> AsyncIOScheduler:
    """
    스케줄러 초기화 및 작업 등록

    Args:
        bot: Discord 봇 인스턴스

    Returns:
        AsyncIOScheduler (started)
    """
    scheduler = AsyncIOScheduler(timezone=KST)

    # 매주 일요일 20:00 KST
    scheduler.add_job(
        func=lambda: _check_weekly_posts(bot),
        trigger=CronTrigger(
            day_of_week="sun",
            hour=20,
            minute=0,
            timezone=KST
        ),
        id="weekly_reminder",
        name="주간 회고 작성 여부 확인",
        replace_existing=True
    )

    scheduler.start()
    print("[scheduler] 주간 리마인더 스케줄러 시작됨 (매주 일요일 KST 20:00)")
    return scheduler


async def _check_weekly_posts(bot: discord.Client):
    """
    등록된 모든 유저의 이번 주 포스트 확인
    미작성 시 재촉 메시지 전송
    """
    print("[scheduler] 주간 포스트 확인 시작...")
    users = get_all_users()

    for user in users:
        if not user.get("weekly_reminder", True):
            continue

        repo = user.get("github_repo")
        posts_path = user.get("posts_path", "_posts")
        channel_id = int(user.get("discord_channel_id") or os.getenv("DISCORD_CHANNEL_ID"))
        user_id = user.get("id", "작성자")

        try:
            has_post = await has_post_this_week(repo, posts_path)

            if not has_post:
                channel = bot.get_channel(channel_id)
                if channel:
                    embed = build_reminder_message(user_id)
                    await channel.send(embed=embed)
                    print(f"[scheduler] 재촉 메시지 전송: {user_id}")
                else:
                    print(f"[scheduler] 채널 없음: {channel_id}")
            else:
                print(f"[scheduler] {user_id}: 이번 주 포스트 있음 ✅")

        except Exception as e:
            print(f"[scheduler] 오류 ({user_id}): {e}")
