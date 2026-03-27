"""
육키티조수육퍼피 Discord 봇 메인
슬래시 커맨드: /add_account, /remove_account, /check_now, /help
"""
from __future__ import annotations

import os
import discord
from discord import app_commands
from dotenv import load_dotenv

from .config_manager import add_user, remove_user, get_user_by_id, get_all_users
from .message_builder import build_welcome_message
from .scheduler import setup_scheduler

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True


class KittyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        """봇 시작 시 슬래시 커맨드 동기화"""
        await self.tree.sync()
        print("[bot] 슬래시 커맨드 동기화 완료")

    async def on_ready(self):
        print(f"[bot] {self.user} 로그인 완료!")
        # 스케줄러 시작
        setup_scheduler(self)
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="회고 작성 여부 👀"
            )
        )


bot = KittyBot()


# ─── 슬래시 커맨드 ───────────────────────────────────────────────────────────

@bot.tree.command(name="add_account", description="깃허브 계정을 등록해서 회고 알림을 받아요!")
@app_commands.describe(
    github_username="GitHub 사용자명 (e.g. 6kitty)",
    github_repo="레포지토리 (e.g. 6kitty/6kitty.github.io)",
    posts_path="포스트 경로 (기본값: _posts)",
    channel="알림 받을 채널 (비워두면 현재 채널)",
    email="이메일 (선택사항)"
)
async def add_account(
    interaction: discord.Interaction,
    github_username: str,
    github_repo: str,
    posts_path: str = "_posts",
    channel: discord.TextChannel = None,
    email: str = ""
):
    await interaction.response.defer(ephemeral=True)

    target_channel = channel or interaction.channel
    user_id = github_username  # GitHub 유저명을 ID로 사용

    success = add_user(
        user_id=user_id,
        github_username=github_username,
        github_repo=github_repo,
        posts_path=posts_path,
        discord_channel_id=str(target_channel.id),
        email=email
    )

    if not success:
        await interaction.followup.send(
            f"⚠️ `{github_username}` 또는 `{github_repo}`는 이미 등록되어 있어요!",
            ephemeral=True
        )
        return

    # 환영 메시지 전송
    embed = build_welcome_message(user_id, github_repo)
    await target_channel.send(embed=embed)

    # GitHub Webhook 설정 안내
    webhook_url = f"http://YOUR_OCI_IP:{os.getenv('WEBHOOK_PORT', '8080')}/webhook/github"
    guide = (
        f"✅ 등록 완료!\n\n"
        f"**마지막 단계:** GitHub Webhook을 설정해야 알림이 와요.\n"
        f"1. `https://github.com/{github_repo}/settings/hooks` 접속\n"
        f"2. **Add webhook** 클릭\n"
        f"3. Payload URL: `{webhook_url}`\n"
        f"4. Content type: `application/json`\n"
        f"5. Secret: `.env`의 `GITHUB_WEBHOOK_SECRET` 값\n"
        f"6. 이벤트: **Just the push event** 선택\n\n"
        f"자세한 설정 가이드는 노션 문서를 참고하세요!"
    )
    await interaction.followup.send(guide, ephemeral=True)


@bot.tree.command(name="remove_account", description="등록된 깃허브 계정을 삭제해요")
@app_commands.describe(github_username="삭제할 GitHub 사용자명")
async def remove_account(interaction: discord.Interaction, github_username: str):
    await interaction.response.defer(ephemeral=True)

    success = remove_user(github_username)

    if success:
        await interaction.followup.send(f"✅ `{github_username}` 계정이 삭제되었어요.", ephemeral=True)
    else:
        await interaction.followup.send(f"⚠️ `{github_username}`를 찾을 수 없어요.", ephemeral=True)


@bot.tree.command(name="check_now", description="지금 바로 이번 주 회고 작성 여부를 확인해요")
@app_commands.describe(github_username="확인할 사용자 (비워두면 전체)")
async def check_now(interaction: discord.Interaction, github_username: str = ""):
    await interaction.response.defer()

    from .github_client import has_post_this_week

    if github_username:
        user = get_user_by_id(github_username)
        if not user:
            await interaction.followup.send(f"⚠️ `{github_username}`를 찾을 수 없어요.")
            return
        users = [user]
    else:
        users = get_all_users()

    results = []
    for user in users:
        has_post = await has_post_this_week(
            user["github_repo"],
            user.get("posts_path", "_posts")
        )
        status = "✅ 작성함" if has_post else "❌ 미작성"
        results.append(f"**{user['id']}**: {status}")

    msg = "**이번 주 회고 현황**\n" + "\n".join(results)
    await interaction.followup.send(msg)


@bot.tree.command(name="list_accounts", description="등록된 모든 계정 목록을 보여줘요")
async def list_accounts(interaction: discord.Interaction):
    users = get_all_users()
    if not users:
        await interaction.response.send_message("등록된 계정이 없어요!", ephemeral=True)
        return

    lines = ["**등록된 계정 목록**"]
    for u in users:
        reminder = "🔔" if u.get("weekly_reminder") else "🔕"
        lines.append(f"{reminder} **{u['id']}** — `{u['github_repo']}`")

    await interaction.response.send_message("\n".join(lines), ephemeral=True)


@bot.tree.command(name="kitty_help", description="육키티조수육퍼피 사용 방법을 알려드려요!")
async def kitty_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌟 육키티조수육퍼피 사용 가이드",
        color=0x7289DA
    )
    embed.add_field(
        name="/add_account",
        value="GitHub 계정 등록 — 회고 포스트 알림 시작",
        inline=False
    )
    embed.add_field(
        name="/remove_account",
        value="등록된 계정 삭제",
        inline=False
    )
    embed.add_field(
        name="/check_now",
        value="이번 주 회고 작성 여부 즉시 확인",
        inline=False
    )
    embed.add_field(
        name="/list_accounts",
        value="등록된 계정 목록 확인",
        inline=False
    )
    embed.add_field(
        name="⏰ 자동 알림",
        value="매주 일요일 KST 20:00 미작성 시 재촉 메시지",
        inline=False
    )
    embed.set_footer(text="꾸준한 기록이 최고의 운세입니다 ✨")
    await interaction.response.send_message(embed=embed, ephemeral=True)
