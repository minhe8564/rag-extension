"""
Runpod 서비스
비즈니스 로직 처리
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.runpod import Runpod
from ..repositories.runpod_repository import RunpodRepository
from ..schemas.request.create_request import RunpodCreateRequest
from ..schemas.request.update_request import RunpodUpdateRequest


def bytes_to_hex(byte_data: bytes) -> str:
    """바이트를 16진수 문자열로 변환"""
    return byte_data.hex() if byte_data else ""


async def create_runpod(
    session: AsyncSession,
    request: RunpodCreateRequest
) -> Runpod:
    runpod = Runpod(
        runpod_no=uuid.uuid4().bytes,
        name=request.name,
        address=request.address,
    )
    
    return await RunpodRepository.save(session, runpod)

async def get_all_runpods(
    session: AsyncSession
) -> list[Runpod]:
    return await RunpodRepository.find_all(session)

async def update_runpod_by_name(
    session: AsyncSession,
    name: str,
    request: RunpodUpdateRequest
) -> Runpod:
    runpod = await RunpodRepository.find_by_name(session, name)
    
    if not runpod:
        raise ValueError("Runpod를 찾을 수 없습니다.")
    
    # 이름과 주소 업데이트
    runpod.name = request.name
    runpod.address = request.address
    
    return await RunpodRepository.update(session, runpod)