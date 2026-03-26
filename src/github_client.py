"""
GitHub API 클라이언트
- 포스트 내용 가져오기
- 이번 주 커밋 여부 확인
"""

import os
import httpx
from datetime import datetime, timedelta
import pytz
import base64
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


async def get_post_content(repo: str, file_path: str) -> tuple[str, str]:
    """
    GitHub API로 포스트 파일 내용 가져오기

    Args:
        repo: "owner/repo" 형식
        file_path: 파일 경로 (e.g. "_posts/2026-03-25-review.md")

    Returns:
        (title, content) 튜플
    """
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

    # base64 디코딩
    content_bytes = base64.b64decode(data["content"])
    content = content_bytes.decode("utf-8")

    # 제목 추출 (Jekyll front matter에서)
    title = _extract_title(content, file_path)

    return title, content


def _extract_title(content: str, file_path: str) -> str:
    """Jekyll front matter에서 제목 추출"""
    lines = content.split("\n")
    in_front_matter = False

    for line in lines:
        if line.strip() == "---":
            in_front_matter = not in_front_matter
            continue
        if in_front_matter and line.startswith("title:"):
            title = line.replace("title:", "").strip().strip('"').strip("'")
            return title

    # front matter에 없으면 파일명에서 추출 (날짜 제거)
    filename = file_path.split("/")[-1].replace(".md", "")
    parts = filename.split("-")
    if len(parts) > 3:
        return " ".join(parts[3:]).replace("-", " ").title()

    return filename


async def has_post_this_week(repo: str, posts_path: str) -> bool:
    """
    이번 주(월~일) `posts_path`에 커밋이 있었는지 확인

    Args:
        repo: "owner/repo" 형식
        posts_path: posts 디렉토리 경로

    Returns:
        bool
    """
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)

    # 이번 주 월요일 00:00 KST
    days_since_monday = now.weekday()
    monday = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
    since = monday.isoformat()

    url = f"https://api.github.com/repos/{repo}/commits"
    params = {
        "path": posts_path,
        "since": since,
        "per_page": 1
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        commits = response.json()

    return len(commits) > 0


def build_post_url(github_username: str, repo_name: str, file_path: str) -> str:
    """
    Jekyll 블로그 포스트 URL 생성

    Args:
        github_username: GitHub 유저명
        repo_name: 레포 이름 (e.g. "6kitty.github.io")
        file_path: 파일 경로 (e.g. "_posts/2026-03-25-weekly-review.md")

    Returns:
        "https://6kitty.github.io/weekly-review" 형태의 URL
    """
    filename = file_path.split("/")[-1].replace(".md", "")
    parts = filename.split("-")

    if len(parts) >= 4:
        # YYYY-MM-DD-title 형식에서 날짜 제거
        slug = "-".join(parts[3:])
        base_url = f"https://{repo_name}"
        return f"{base_url}/{slug}"

    return f"https://{repo_name}"
