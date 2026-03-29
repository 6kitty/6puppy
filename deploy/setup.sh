#!/bin/bash
# ============================
# 육키티조수육퍼피 OCI VM 초기 세팅 스크립트
# Ubuntu 20.04/22.04 기준
# ============================

set -e

echo "🚀 육키티조수육퍼피 봇 설치 시작..."

# 1. 시스템 패키지 업데이트
sudo apt update && sudo apt upgrade -y
sudo apt install -y software-properties-common git

# 2. Python 3.10 설치 및 선택
PYTHON_CMD=python3
if command -v python3.10 >/dev/null 2>&1; then
    PYTHON_CMD=python3.10
else
    if grep -qE '^VERSION_ID="?20\.04"?' /etc/os-release 2>/dev/null; then
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt update
        sudo apt install -y python3.10 python3.10-venv python3.10-distutils
        PYTHON_CMD=python3.10
    else
        sudo apt install -y python3 python3-venv python3-pip
    fi
fi

# 3. 프로젝트 클론 (또는 이미 있으면 pull)
if [ -d "/home/ubuntu/6puppy" ]; then
    echo "📦 기존 설치 감지 - git pull 실행"
    cd /home/ubuntu/6puppy
    git pull
else
    echo "📦 프로젝트 클론"
    cd /home/ubuntu
    git clone https://github.com/6kitty/6puppy.git
    cd 6puppy
fi

# 4. 가상환경 생성 및 패키지 설치
$PYTHON_CMD -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. .env 파일 확인
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  .env 파일을 생성했습니다. 값을 직접 채워주세요:"
    echo "   nano /home/ubuntu/6kitty-bot/.env"
fi

# 5. systemd 서비스 등록
sudo cp deploy/6kitty-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 6kitty-bot
sudo systemctl start 6kitty-bot

# 6. 방화벽 (OCI는 Security List도 별도로 열어야 함!)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8080 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || true

echo "✅ 설치 완료!"
echo ""
echo "상태 확인: sudo systemctl status 6kitty-bot"
echo "로그 보기: sudo journalctl -u 6kitty-bot -f"
echo ""
echo "⚠️  OCI 콘솔에서 Security List 8080 포트도 열어주세요!"
