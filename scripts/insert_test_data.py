"""
테스트 데이터 삽입 스크립트
RAG Strategy 테스트를 위한 샘플 데이터를 DB에 삽입합니다.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .env 파일을 먼저 로드 (import 전에 해야함)
env_path = project_root / ".env"
load_dotenv(env_path)

from app.common.db import AsyncSessionLocal, engine
from app.domains.rag_setting.models.strategy import StrategyType, Strategy, generate_uuid_binary
from sqlalchemy import select


async def insert_test_data():
    """테스트 데이터를 데이터베이스에 삽입"""

    async with AsyncSessionLocal() as session:
        try:
            print("=" * 60)
            print("RAG 전략 테스트 데이터 삽입 시작")
            print("=" * 60)

            # 1. 기존 StrategyType 조회
            print("\n[Step 1] 기존 StrategyType 조회 중...")

            strategy_type_names = [
                "extraction", "chunking", "embedding", "transformation",
                "retrieval", "reranking", "prompting", "generation"
            ]

            strategy_types_map = {}
            for type_name in strategy_type_names:
                result = await session.execute(
                    select(StrategyType).where(StrategyType.name == type_name)
                )
                strategy_type = result.scalar_one_or_none()

                if strategy_type:
                    strategy_types_map[type_name] = strategy_type
                    print(f"  ✓ '{type_name}' 조회 완료")
                else:
                    print(f"  ⚠️ '{type_name}' 타입을 찾을 수 없습니다. DB에 먼저 생성해주세요.")

            print(f"\n✅ StrategyType {len(strategy_types_map)}개 조회 완료\n")

            # 2. Strategy 테스트 데이터 생성
            strategies_data = [
                # Extraction 전략
                {
                    "type": "extraction",
                    "name": "PyPDF 텍스트 추출",
                    "description": "PyPDF 라이브러리를 사용한 PDF 텍스트 추출",
                    "parameter": {"library": "pypdf", "mode": "text"}
                },
                {
                    "type": "extraction",
                    "name": "Unstructured 파일 파싱",
                    "description": "Unstructured 라이브러리를 사용한 다양한 파일 형식 파싱",
                    "parameter": {"library": "unstructured", "mode": "auto"}
                },

                # Chunking 전략
                {
                    "type": "chunking",
                    "name": "고정 크기 청킹",
                    "description": "지정된 토큰 수로 텍스트를 균등하게 분할",
                    "parameter": {"chunk_size": 512, "overlap": 50}
                },
                {
                    "type": "chunking",
                    "name": "의미 기반 청킹",
                    "description": "문장 및 단락 구조를 고려한 의미 단위 분할",
                    "parameter": {"method": "semantic", "threshold": 0.7}
                },
                {
                    "type": "chunking",
                    "name": "재귀적 문자 분할",
                    "description": "문단, 문장, 단어 순서로 재귀적으로 텍스트 분할",
                    "parameter": {"separators": ["\\n\\n", "\\n", ". ", " "], "chunk_size": 1000}
                },

                # Embedding 전략
                {
                    "type": "embedding",
                    "name": "OpenAI Embeddings",
                    "description": "OpenAI의 text-embedding-ada-002 모델 사용",
                    "parameter": {"model": "text-embedding-ada-002", "dimensions": 1536}
                },
                {
                    "type": "embedding",
                    "name": "HuggingFace Embeddings",
                    "description": "HuggingFace 오픈소스 임베딩 모델 사용",
                    "parameter": {"model": "sentence-transformers/all-MiniLM-L6-v2", "dimensions": 384}
                },

                # Retrieval 전략
                {
                    "type": "retrieval",
                    "name": "벡터 유사도 검색",
                    "description": "코사인 유사도 기반 벡터 검색",
                    "parameter": {"metric": "cosine", "top_k": 5}
                },
                {
                    "type": "retrieval",
                    "name": "하이브리드 검색",
                    "description": "벡터 검색과 키워드 검색 결합",
                    "parameter": {"vector_weight": 0.7, "keyword_weight": 0.3, "top_k": 10}
                },

                # Reranking 전략
                {
                    "type": "reranking",
                    "name": "Cross-Encoder 재순위",
                    "description": "Cross-Encoder 모델을 사용한 검색 결과 재순위",
                    "parameter": {"model": "cross-encoder/ms-marco-MiniLM-L-6-v2", "top_k": 3}
                },
                {
                    "type": "reranking",
                    "name": "MMR 다양성 재순위",
                    "description": "Maximal Marginal Relevance 기반 다양성 확보",
                    "parameter": {"lambda_param": 0.5, "top_k": 5}
                },

                # Generation 전략
                {
                    "type": "generation",
                    "name": "GPT-4 생성",
                    "description": "OpenAI GPT-4를 사용한 답변 생성",
                    "parameter": {"model": "gpt-4", "temperature": 0.7, "max_tokens": 500}
                },
                {
                    "type": "generation",
                    "name": "Claude 생성",
                    "description": "Anthropic Claude를 사용한 답변 생성",
                    "parameter": {"model": "claude-3-opus", "temperature": 0.5, "max_tokens": 1000}
                },
            ]

            print("[Step 2] Strategy 데이터 삽입 중...")

            inserted_count = 0
            skipped_count = 0
            missing_type_count = 0

            for strategy_data in strategies_data:
                # 해당 타입 찾기
                strategy_type_obj = strategy_types_map.get(strategy_data["type"])

                if not strategy_type_obj:
                    print(f"  ⚠️ '{strategy_data['name']}' 스킵 ('{strategy_data['type']}' 타입 없음)")
                    missing_type_count += 1
                    continue

                # 이미 존재하는지 확인 (이름으로)
                result = await session.execute(
                    select(Strategy).where(Strategy.name == strategy_data["name"])
                )
                existing_strategy = result.scalar_one_or_none()

                if existing_strategy:
                    print(f"  - '{strategy_data['name']}' 이미 존재 (스킵)")
                    skipped_count += 1
                    continue

                # Strategy 생성
                strategy = Strategy(
                    strategy_no=generate_uuid_binary(),
                    strategy_type_no=strategy_type_obj.strategy_type_no,
                    name=strategy_data["name"],
                    description=strategy_data["description"],
                    parameter=strategy_data["parameter"]
                )
                session.add(strategy)
                print(f"  ✓ '{strategy_data['name']}' ({strategy_data['type']}) 생성")
                inserted_count += 1

            await session.commit()

            print(f"\n✅ Strategy 삽입 완료:")
            print(f"   - 새로 삽입: {inserted_count}개")
            print(f"   - 이미 존재: {skipped_count}개")
            if missing_type_count > 0:
                print(f"   - 타입 없어서 스킵: {missing_type_count}개")

            # 3. 삽입된 데이터 확인
            print("\n[Step 3] 삽입된 데이터 확인...")

            for type_name in strategy_type_names:
                result = await session.execute(
                    select(Strategy)
                    .join(StrategyType)
                    .where(StrategyType.name == type_name)
                )
                strategies = result.scalars().all()
                if strategies:
                    print(f"\n  📁 {type_name}: {len(strategies)}개 전략")
                    for strategy in strategies:
                        print(f"     - {strategy.name}")

            print("\n" + "=" * 60)
            print("✅ 테스트 데이터 삽입 완료!")
            print("=" * 60)
            print("\n다음 명령어로 API 테스트를 진행하세요:")
            print("  curl -H \"x-user-role: USER\" \"http://localhost:8000/rag/strategies?pageNum=1&pageSize=5\"")
            print("\n또는 Swagger UI에서 테스트:")
            print("  http://localhost:8000/docs")
            print("=" * 60)

        except Exception as e:
            await session.rollback()
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    """메인 실행 함수"""
    try:
        # 데이터베이스 연결 테스트
        async with engine.connect() as conn:
            print("✅ 데이터베이스 연결 성공\n")

        # 테스트 데이터 삽입
        await insert_test_data()

    except Exception as e:
        print(f"\n❌ 실행 실패: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
