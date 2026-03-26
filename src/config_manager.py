"""
유저 설정 관리 (config.yaml CRUD)
"""

import yaml
import os
from typing import Optional

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")


def load_config() -> dict:
    """config.yaml 로드"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config: dict):
    """config.yaml 저장"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def get_all_users() -> list:
    """등록된 모든 유저 목록"""
    config = load_config()
    return config.get("users", [])


def get_user_by_repo(repo_full_name: str) -> Optional[dict]:
    """레포 이름으로 유저 찾기 (e.g. '6kitty/6kitty.github.io')"""
    for user in get_all_users():
        if user.get("github_repo") == repo_full_name:
            return user
    return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    """유저 ID로 유저 찾기"""
    for user in get_all_users():
        if user.get("id") == user_id:
            return user
    return None


def add_user(
    user_id: str,
    github_username: str,
    github_repo: str,
    posts_path: str = "_posts",
    discord_channel_id: str = "",
    email: str = "",
    weekly_reminder: bool = True
) -> bool:
    """
    새 유저 등록

    Returns:
        True if added, False if already exists
    """
    config = load_config()
    users = config.get("users", [])

    # 중복 체크
    for user in users:
        if user.get("id") == user_id or user.get("github_repo") == github_repo:
            return False

    new_user = {
        "id": user_id,
        "github_username": github_username,
        "github_repo": github_repo,
        "posts_path": posts_path,
        "discord_channel_id": discord_channel_id,
        "email": email,
        "weekly_reminder": weekly_reminder,
        "timezone": "Asia/Seoul",
        "reminder_day": 6,
        "reminder_hour": 20
    }

    users.append(new_user)
    config["users"] = users
    save_config(config)
    return True


def remove_user(user_id: str) -> bool:
    """유저 삭제"""
    config = load_config()
    users = config.get("users", [])
    original_len = len(users)

    config["users"] = [u for u in users if u.get("id") != user_id]
    save_config(config)

    return len(config["users"]) < original_len
