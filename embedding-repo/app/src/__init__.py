"""
Embedding Strategy 모듈
전략별 임베딩 로직을 담고 있습니다.
"""

from .base import BaseEmbeddingStrategy
from .dense import Dense

__all__ = [
    "BaseEmbeddingStrategy",
    "Dense"
]

