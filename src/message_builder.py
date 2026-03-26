"""
디스코드 메시지 빌더
지킬앤하이드 컨셉: 칭찬 모드(아침별점) / 재촉 모드(팩트 사이다)
"""

import discord
from datetime import datetime


def build_post_notification(
    author: str,
    title: str,
    url: str,
    summary: str,
    post_date: str = None
) -> discord.Embed:
    """
    ☀️ 칭찬 모드: 포스트 커밋 시 아침별점 스타일 메시지

    Args:
        author: 작성자 닉네임 (e.g. "6kitty")
        title: 포스트 제목
        url: 포스트 URL
        summary: Claude가 생성한 요약
        post_date: 포스트 날짜 (선택)

    Returns:
        discord.Embed
    """
    embed = discord.Embed(
        title="✨ 오늘의 별이 빛나고 있어요 ✨",
        color=0xFFD700  # 황금색
    )

    embed.add_field(
        name="",
        value=(
            f"**{author}님**이 이번 주 회고를 남기셨군요!\n"
            f"작은 기록 하나가 큰 성장으로 이어질 수 있는 날이에요.\n"
            f"꾸준함이야말로 가장 강력한 행운의 아이템이랍니다 🍀"
        ),
        inline=False
    )

    embed.add_field(
        name="📝 이번 글 요약",
        value=summary,
        inline=False
    )

    embed.add_field(
        name="🔗 바로가기",
        value=f"[{title}]({url})",
        inline=False
    )

    embed.add_field(
        name="오늘의 행운 포인트",
        value="커밋을 남긴 당신의 성실함 ⭐",
        inline=False
    )

    embed.set_footer(text=f"육키티조수육퍼피 | {post_date or datetime.now().strftime('%Y.%m.%d')}")

    return embed


def build_reminder_message(author: str) -> discord.Embed:
    """
    🔥 재촉 모드: 일요일 20시 미작성 시 팩트 사이다 메시지

    Args:
        author: 작성자 닉네임

    Returns:
        discord.Embed
    """
    embed = discord.Embed(
        title="🚨 긴급 속보 🚨",
        color=0xFF4444  # 빨간색
    )

    embed.add_field(
        name="",
        value=(
            f"**{author}님** 이번 주 회고 **0건**입니다.\n"
            f"일요일 저녁 8시. 제가 지금 웃고 있는 거 같으세요?\n\n"
            f"침대에서 뒹굴거리고 계신 거 다 보여요.\n"
            f"핸드폰 내려놓고 노트북 여세요. 지금 당장."
        ),
        inline=False
    )

    embed.add_field(
        name="",
        value=(
            "마감은 기다려주지 않습니다.\n"
            "당신의 미래도요. ⏰"
        ),
        inline=False
    )

    embed.add_field(
        name="✍️ 할 일",
        value="`_posts` 폴더에 지금 바로 뭐라도 쓰기",
        inline=False
    )

    embed.set_footer(text="육키티조수육퍼피 | 당신을 걱정하기 때문이에요 (진심)")

    return embed


def build_welcome_message(author: str, repo: str) -> discord.Embed:
    """
    /add_account 등록 완료 환영 메시지
    """
    embed = discord.Embed(
        title="🌟 새로운 별이 등록되었어요!",
        color=0x7289DA  # Discord 블루
    )

    embed.add_field(
        name="",
        value=(
            f"**{author}님**, 이제부터 제가 지켜볼게요.\n"
            f"열심히 기록하는 모습, 응원하고 있답니다 💪\n\n"
            f"📁 감시 대상: `{repo}`\n"
            f"⏰ 마감: 매주 일요일 KST 20:00"
        ),
        inline=False
    )

    embed.set_footer(text="육키티조수육퍼피 | 꾸준한 기록이 최고의 운세입니다")

    return embed
