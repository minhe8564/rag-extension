from __future__ import annotations

import logging
import uuid
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sqla_delete

from app.core.clients.minio_client import remove_object
from app.core.config.settings import settings
from app.core.clients.milvus_client import delete_by_expr
from app.domains.collection.models.collection import Collection
from app.domains.file.models.file import File


logger = logging.getLogger(__name__)


def _uuid_bytes_to_str(b: bytes) -> str:
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


async def _load_children_by_source(
    session: AsyncSession,
    source_file_no: bytes,
) -> List[File]:
    stmt = select(File).where(File.source_no == source_file_no)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def delete_file_entity(
    session: AsyncSession,
    *,
    file_row: File,
    user_role: Optional[str] = None,
) -> None:
    """Delete a single file and its derived children.

    - SOURCE_NO 로 참조하는 자식 파일들을 먼저 DB 에서 삭제한 뒤, 부모 파일을 삭제.
    - 이후 Milvus 컬렉션(문서용 및 이미지용)과 MinIO 객체를 삭제.
    - Milvus / MinIO 단계에서 예외가 발생하면 그대로 전파하여 전체 트랜잭션을 롤백.
    """
    # 1) SOURCE_NO 로 참조하는 자식 파일들 조회 (MinIO / Milvus 정리에 사용)
    logger.warning(
        "Starting delete_file_entity for source file %s",
        _uuid_bytes_to_str(file_row.file_no),
    )
    child_files = await _load_children_by_source(session, file_row.file_no)
    logger.warning(
        "Loaded %d child files for source file %s",
        len(child_files),
        _uuid_bytes_to_str(file_row.file_no),
    )

    # 2) DB에서 자식 → 부모 순으로 명시적으로 삭제
    #    FK (ON DELETE RESTRICT) 때문에 반드시 자식을 먼저 지워야 함.
    if child_files:
        logger.warning(
            "Deleting %d child DB rows for source file %s",
            len(child_files),
            _uuid_bytes_to_str(file_row.file_no),
        )
        await session.execute(
            sqla_delete(File).where(File.source_no == file_row.file_no)
        )
        await session.flush()

    logger.warning(
        "Deleting source DB row for file %s",
        _uuid_bytes_to_str(file_row.file_no),
    )
    await session.delete(file_row)
    await session.flush()

    # 3) Milvus 벡터 삭제

    # 3-1) 부모 파일에 대한 기존 규칙 기반 삭제
    milvus_collection_name: Optional[str] = None
    partition_name: Optional[str] = None

    special_partitions = {"hebees", "public"}
    coll_name: Optional[str] = None
    if getattr(file_row, "collection_no", None):
        logger.warning(
            "Source file %s has collection_no; resolving collection row",
            _uuid_bytes_to_str(file_row.file_no),
        )
        try:
            coll = await session.get(Collection, file_row.collection_no)
            coll_name = getattr(coll, "name", None) if coll else None
        except Exception:
            coll_name = None

    if coll_name in special_partitions:
        milvus_collection_name = "publicRetina_1"
        partition_name = coll_name  # 'hebees' or 'public'
    else:
        # Offer-based dedicated collection, e.g., h{offer_no}_1
        offer_no = getattr(file_row, "offer_no", None) or ""
        if offer_no:
            milvus_collection_name = f"h{offer_no}_1"

    if milvus_collection_name:
        file_no_str = _uuid_bytes_to_str(file_row.file_no)
        pk_field = getattr(settings, "milvus_pk_field", "file_no") or "file_no"
        path_field = getattr(settings, "milvus_path_field", "path") or "path"

        expr1 = f"{pk_field} == '{file_no_str}'"
        logger.warning(
            "Deleting Milvus vectors for source file %s from collection %s (partition=%s) with expr=%s",
            file_no_str,
            milvus_collection_name,
            partition_name,
            expr1,
        )
        delete_by_expr(milvus_collection_name, expr1, partition_name=partition_name)
    else:
        logger.warning("Milvus target for source file could not be resolved; skipping vector deletion for source.")

    # 3-2) SOURCE_NO 자식 파일들에 대한 이미지 컬렉션 삭제
    # 이미지 벡터는 "부모 문서의 FILE_NO" 를 PK 로 사용하므로,
    # h{offerNo}_image_{versionNo} / publicRetina_image_{versionNo} 컬렉션에서
    # 부모 file_no 기준으로 삭제한다.
    image_collection_name: Optional[str] = None
    image_pk_field = getattr(settings, "milvus_pk_field", "file_no") or "file_no"

    if getattr(file_row, "collection_no", None):
        img_coll = await session.get(Collection, file_row.collection_no)
        if img_coll:
            base_name = (getattr(img_coll, "name", "") or "").strip()
            version = getattr(img_coll, "version", None)
            logger.warning(
                "Resolved parent collection for images: base_name=%s, version=%s for source file %s",
                base_name,
                version,
                _uuid_bytes_to_str(file_row.file_no),
            )
            if version is not None:
                if base_name in {"public", "hebees"} :
                    # public / hebees 컬렉션은 모두 publicRetina_image_{version} 안의 파티션으로 저장됨
                    image_collection_name = f"publicRetina_image_{version}"
                elif base_name.startswith("h"):
                    # h{offerNo} -> h{offerNo}_image_{version}
                    image_collection_name = f"{base_name}_image_{version}"

    if image_collection_name and child_files:
        parent_file_no_str = _uuid_bytes_to_str(file_row.file_no)
        expr_child = f"{image_pk_field} == '{parent_file_no_str}'"
        logger.warning(
            "Resolved image collection name '%s' for %d child files of source file %s; deleting by parent file_no with expr=%s (no partition filter)",
            image_collection_name,
            len(child_files),
            _uuid_bytes_to_str(file_row.file_no),
            expr_child,
        )

        # 이미지 컬렉션 삭제 시에는 partition 을 지정하지 않고 전체 파티션에서 삭제
        logger.warning(
            "Deleting Milvus image-vectors for parent file %s from image collection %s with expr=%s",
            parent_file_no_str,
            image_collection_name,
            expr_child,
        )
        delete_by_expr(image_collection_name, expr_child)
    else:
        if child_files:
            logger.warning(
                "Image collection name could not be resolved from parent collection; "
                "skipping image-vector deletion for %d child files.",
                len(child_files),
            )

    # 4) MinIO 객체 삭제 (부모 + 자식들 모두)
    all_files = child_files + [file_row]
    for f in all_files:
        logger.info(
            "Deleting MinIO object for file %s (bucket=%s, path=%s)",
            _uuid_bytes_to_str(f.file_no),
            getattr(f, "bucket", None),
            getattr(f, "path", None),
        )
        remove_object(f.bucket, f.path)
