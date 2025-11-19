from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.file import File
from typing import List, Dict


class FileService:
    async def get_files_by_ids(
        self, 
        db: AsyncSession, 
        file_ids: List[int]
    ) -> List[File]:
        """파일 ID 리스트로 파일 정보 조회"""
        # file_ids는 정수 리스트이지만, 실제로는 FILE_NO (BINARY(16))를 사용해야 함
        # 일단 모든 파일을 조회하고 필터링 (임시 처리)
        stmt = select(File)
        result = await db.execute(stmt)
        all_files = result.scalars().all()
        # file_no를 hex로 변환하여 매칭
        return [f for f in all_files if f.file_no.hex() in [str(fid) for fid in file_ids]]
    
    def group_files_by_type(self, files: List[File]) -> Dict[str, List[str]]:
        """파일들을 타입별로 그룹화"""
        grouped = {
            "pdf": [],
            "xlsx": [],
            "docs": [],
            "txt": []
        }
        
        for file in files:
            file_type = file.file_extension.lower()
            file_no = file.file_no.hex() if isinstance(file.file_no, bytes) else str(file.file_no)
            # 확장자 정규화
            if file_type == "pdf":
                grouped["pdf"].append(file_no)
            elif file_type in ["xlsx", "xls"]:
                grouped["xlsx"].append(file_no)
            elif file_type in ["doc", "docx"]:
                grouped["docs"].append(file_no)
            elif file_type == "txt":
                grouped["txt"].append(file_no)
        
        return grouped

