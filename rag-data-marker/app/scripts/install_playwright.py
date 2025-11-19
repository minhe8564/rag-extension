#!/usr/bin/env python3
"""
Playwright Chromium 브라우저 설치 스크립트
uv run install-playwright 또는 python -m app.scripts.install_playwright로 실행
"""
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def install_playwright_browser():
    """Playwright Chromium 브라우저 설치"""
    try:
        logger.info("Playwright Chromium 브라우저 설치 시작...")
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            timeout=300
        )
        logger.info("Playwright Chromium 브라우저 설치 완료")
        return 0
    except subprocess.TimeoutExpired:
        logger.error("Playwright 브라우저 설치 시간 초과 (5분)")
        return 1
    except subprocess.CalledProcessError as e:
        logger.error(f"Playwright 브라우저 설치 실패: {e}")
        return 1
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(install_playwright_browser())

