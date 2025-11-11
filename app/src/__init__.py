"""
Generation Strategy 모듈
전략별 답변 생성 로직을 담고 있습니다.
"""

from .base import BaseGenerationStrategy
from .openAI import OpenAI
from .ollama import Ollama

__all__ = [
    "BaseGenerationStrategy",
    "OpenAI",
    "Ollama"
]

