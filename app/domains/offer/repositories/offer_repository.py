"""
OFFER 테이블 조회 Repository
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.offer import Offer


class OfferRepository:
    @staticmethod
    async def find_by_offer_no(
        db: AsyncSession,
        offer_no: str
    ) -> Optional[Offer]:
        result = await db.execute(
            select(Offer).where(Offer.offer_no == offer_no)
        )
        return result.scalar_one_or_none()
