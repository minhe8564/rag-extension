from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility
)
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
import json


class MilvusService:
    """Milvus 컬렉션 관리 및 데이터 삽입 서비스"""
    
    def __init__(self, host: str = "localhost", port: int = 19530):
        self.host = host
        self.port = port
        self._connected = False
    
    def connect(self):
        """Milvus 서버에 연결"""
        if not self._connected:
            try:
                connections.connect(
                    alias="default",
                    host=self.host,
                    port=self.port
                )
                self._connected = True
                logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"Failed to connect to Milvus: {str(e)}")
                raise
    
    def ensure_collection(self, collection_name: str, vector_dim: int = 1024) -> tuple[Collection, bool]:
        """
        컬렉션이 존재하는지 확인하고, 없으면 생성
        
        Args:
            collection_name: 컬렉션 이름
            vector_dim: 벡터 차원 (임베딩 벡터 크기)
        
        Returns:
            (Collection 객체, is_newly_created: bool) 튜플
        """
        self.connect()
        
        # 컬렉션 존재 여부 확인
        is_newly_created = False
        if utility.has_collection(collection_name):
            logger.info(f"Collection '{collection_name}' already exists")
            collection = Collection(collection_name)
        else:
            is_newly_created = True
            logger.info(f"Creating collection '{collection_name}' with vector_dim={vector_dim}")
            
            # 필드 스키마 정의
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="file_no", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=vector_dim),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
            ]
            
            # 컬렉션 스키마 생성
            schema = CollectionSchema(
                fields=fields,
                description=f"Embedding collection: {collection_name}"
            )
            
            # 컬렉션 생성
            collection = Collection(name=collection_name, schema=schema)
            
            # 인덱스 생성 (HNSW 인덱스)
            index_params = {
                "metric_type": "L2",
                "index_type": "HNSW",
                "params": {"M": 16, "efConstruction": 200}
            }
            collection.create_index(field_name="vector", index_params=index_params)
            
            logger.info(f"Collection '{collection_name}' created successfully")
        
        # 컬렉션 로드
        if not collection.has_index():
            # 인덱스가 없으면 생성
            index_params = {
                "metric_type": "COSINE",
                "index_type": "HNSW",
                "params": {"M": 16, "efConstruction": 200}
            }
            collection.create_index(field_name="vector", index_params=index_params)
        
        collection.load()
        logger.info(f"Collection '{collection_name}' loaded")
        
        return collection, is_newly_created
    
    def ensure_partitions(self, collection_name: str, partitions: List[str]) -> None:
        """컬렉션에 필요한 파티션이 없으면 생성"""
        self.connect()
        if not utility.has_collection(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist")
        collection = Collection(collection_name)
        for p in partitions or []:
            try:
                if not collection.has_partition(p):
                    collection.create_partition(p)
                    logger.info(f"Created partition '{p}' in collection '{collection_name}'")
            except Exception as e:
                logger.warning(f"Partition ensure failed for '{p}' in '{collection_name}': {str(e)}")
    
    def insert_embeddings(
        self,
        collection_name: str,
        embeddings: List[Dict[str, Any]],
        vector_dim: int = 1024,
        partition_name: Optional[str] = None
    ) -> bool:
        """
        임베딩 데이터를 Milvus에 삽입
        
        Args:
            collection_name: 컬렉션 이름
            embeddings: 삽입할 데이터 리스트
                각 항목은 {
                    "name": str (파일명),
                    "text": str (청크 텍스트),
                    "vector": List[float] (임베딩 벡터),
                    "metadata": Dict (PAGE_NO, chunk_id, CREATED_AT, UPDATED_AT)
                } 형식
        
        Returns:
            성공 여부
        """
        try:
            collection, _ = self.ensure_collection(collection_name, vector_dim)
            
            # 데이터 준비 (입력 값 보정 및 검증)
            file_nos: List[str] = []
            texts: List[str] = []
            vectors: List[List[float]] = []
            metadata_list: List[str] = []

            for index, emb in enumerate(embeddings):
                # file_no는 문자열이어야 함. 다양한 키를 허용하고, None은 빈 문자열로 보정
                raw_file_no = (
                    emb.get("file_no")
                    or emb.get("name")
                    or emb.get("file_id")
                    or emb.get("fileId")
                    or emb.get("doc_id")
                )
                file_no_str = "" if raw_file_no is None else str(raw_file_no)
                file_nos.append(file_no_str)

                # text는 문자열이어야 함. None이면 빈 문자열로 보정
                raw_text = emb.get("text")
                text_str = "" if raw_text is None else str(raw_text)
                texts.append(text_str)

                # vector는 필수. 길이가 다르면 보정(부족하면 0 패딩, 길면 잘라냄)
                raw_vector = emb.get("vector")
                if raw_vector is None:
                    raise ValueError(f"embedding[{index}] has no 'vector' field")
                vec = list(map(float, raw_vector))
                if len(vec) < vector_dim:
                    vec = vec + [0.0] * (vector_dim - len(vec))
                elif len(vec) > vector_dim:
                    vec = vec[:vector_dim]
                vectors.append(vec)

                # metadata를 JSON 문자열로 변환 (None → {})
                metadata_json = json.dumps(emb.get("metadata", {}) or {}, ensure_ascii=False)
                metadata_list.append(metadata_json)
            
            # 데이터 삽입
            insert_data = [file_nos, texts, vectors, metadata_list]
            if partition_name:
                collection.insert(insert_data, partition_name=partition_name)
            else:
                collection.insert(insert_data)
            
            # 플러시하여 즉시 반영
            collection.flush()
            
            logger.info(f"Inserted {len(embeddings)} embeddings into collection '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert embeddings into Milvus: {str(e)}", exc_info=True)
            raise
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """컬렉션 통계 정보 조회"""
        try:
            self.connect()
            if not utility.has_collection(collection_name):
                return {"exists": False}
            
            collection = Collection(collection_name)
            collection.load()
            
            stats = {
                "exists": True,
                "num_entities": collection.num_entities,
                "is_empty": collection.is_empty,
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {"error": str(e)}



