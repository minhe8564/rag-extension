from app.service.gateway_client import GatewayClient
from app.schemas.request.queryRequest import QueryProcessRequest
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from loguru import logger


class QueryService:
    def __init__(self):
        self.gateway_client = GatewayClient()
    
    async def process_query(
        self,
        request: QueryProcessRequest,
        db: AsyncSession
    ) -> Dict[Any, Any]:
        """
        Query 요청 처리: query-embedding -> search -> cross-encoder -> generation 순서로 처리
        
        Args:
            request: QueryProcessRequest
            db: 데이터베이스 세션
        
        Returns:
            최종 generation 결과
        """
        logger.info("Starting query pipeline for query: {}", request.query)
        
        try:
            # 1) Query Embedding
            logger.debug("Step 1: Query Embedding")
            query_embedding_response = await self.gateway_client.request_query_embedding(
                query=request.query,
                strategy=request.queryEmbeddingStrategy,
                parameters=request.queryEmbeddingParameter
            )
            logger.info("Query embedding completed")
            
            # query_embedding_response에서 embedding 추출
            embedding = query_embedding_response.get("result", {}).get("embedding", [])
            
            # 2) Search (Milvus에서 candidate embeddings 검색)
            logger.debug("Step 2: Search")
            search_response = await self.gateway_client.request_search(
                embedding=embedding,
                collection_name=request.collectionName,
                strategy=request.searchStrategy,
                parameters=request.searchParameter
            )
            logger.info("Search completed")
            
            # search_response에서 candidate embeddings 추출
            candidate_embeddings = search_response.get("result", {}).get("candidateEmbeddings", [])
            
            # 3) Cross Encoder
            logger.debug("Step 3: Cross Encoder")
            cross_encoder_response = await self.gateway_client.request_cross_encoder(
                query=request.query,
                candidate_embeddings=candidate_embeddings,
                strategy=request.crossEncoderStrategy,
                parameters=request.crossEncoderParameter
            )
            logger.info("Cross encoder completed")
            
            # 4) Generation
            logger.debug("Step 4: Generation")
            # cross_encoder_response에서 retrieved_chunks 추출
            retrieved_chunks = cross_encoder_response.get("result", {}).get("retrievedChunks", [])
            
            generation_response = await self.gateway_client.request_generation(
                query=request.query,
                retrieved_chunks=retrieved_chunks,
                strategy=request.generationStrategy,
                parameters=request.generationParameter
            )
            logger.info("Generation completed")
            
            # generation_response에서 최종 결과 추출
            generation_result = generation_response.get("result", {})
            
            return {
                "query": generation_result.get("query", request.query),
                "answer": generation_result.get("answer", ""),
                "citations": generation_result.get("citations", [])
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            raise

