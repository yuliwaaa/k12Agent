"""ChromaDB 知识库：按学段切块、入库与检索。"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHROMA_DIR, KNOWLEDGE_DIR, RAG_TOP_K, ensure_data_dirs

logger = logging.getLogger(__name__)

GRADE_TO_DIR = {
    "小学低年级": "grade_1_3",
    "小学高年级": "grade_4_6",
    "初中": "grade_7_9",
    "高中": "grade_10_12",
}

_collection = None
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client

    ensure_data_dirs()
    import chromadb
    from chromadb.config import Settings

    _client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    return _client


def _get_chroma():
    global _collection
    if _collection is not None:
        return _collection

    client = _get_client()
    _collection = client.get_or_create_collection(
        name="k12_knowledge",
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def _doc_id(grade_key: str, path: Path, chunk_index: int) -> str:
    raw = f"{grade_key}:{path.as_posix()}:{chunk_index}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def list_knowledge_files(grade: str | None = None) -> list[Path]:
    if not KNOWLEDGE_DIR.exists():
        return []
    if grade:
        folder = KNOWLEDGE_DIR / GRADE_TO_DIR.get(grade, "")
        if not folder.exists():
            return []
        return sorted(folder.glob("*.md"))
    files: list[Path] = []
    for folder in sorted(KNOWLEDGE_DIR.glob("grade_*")):
        files.extend(sorted(folder.glob("*.md")))
    return files


def build_index(force: bool = False) -> dict[str, int]:
    """扫描 knowledge_base 并写入 Chroma。返回统计信息。"""
    global _collection
    collection = _get_chroma()
    if force:
        client = _get_client()
        try:
            client.delete_collection("k12_knowledge")
        except Exception:  # noqa: BLE001
            pass
        _collection = None
        collection = _get_chroma()

    if collection.count() > 0 and not force:
        return {"chunks": collection.count(), "files": 0, "skipped": 1}

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
        separators=["\n## ", "\n### ", "\n\n", "\n", "。", "！", "？", " "],
    )

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    file_count = 0

    for grade_name, dir_name in GRADE_TO_DIR.items():
        folder = KNOWLEDGE_DIR / dir_name
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue
            file_count += 1
            chunks = splitter.split_text(text)
            for i, chunk in enumerate(chunks):
                ids.append(_doc_id(dir_name, path, i))
                documents.append(chunk)
                metadatas.append(
                    {
                        "grade": grade_name,
                        "grade_key": dir_name,
                        "source": path.name,
                        "title": path.stem,
                    }
                )

    if documents:
        # Chroma 批量上限，分批写入
        batch = 100
        for start in range(0, len(documents), batch):
            end = start + batch
            collection.upsert(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )

    logger.info("知识库入库完成：files=%s chunks=%s", file_count, len(documents))
    return {"chunks": len(documents), "files": file_count, "skipped": 0}


def retrieve(query: str, grade: str, top_k: int = RAG_TOP_K) -> list[dict]:
    """按学段过滤检索相关知识点。"""
    query = (query or "").strip()
    if not query:
        return []

    try:
        collection = _get_chroma()
        if collection.count() == 0:
            build_index()
        if collection.count() == 0:
            return []

        result = collection.query(
            query_texts=[query],
            n_results=min(top_k, max(collection.count(), 1)),
            where={"grade": grade} if grade else None,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("RAG 检索失败：%s", exc)
        return []

    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    dists = (result.get("distances") or [[]])[0]

    items: list[dict] = []
    for doc, meta, dist in zip(docs, metas, dists):
        items.append(
            {
                "content": doc,
                "source": (meta or {}).get("source", ""),
                "title": (meta or {}).get("title", ""),
                "grade": (meta or {}).get("grade", grade),
                "distance": dist,
            }
        )
    return items


def format_context(items: list[dict]) -> str:
    if not items:
        return ""
    parts = []
    for i, item in enumerate(items, 1):
        title = item.get("title") or item.get("source") or f"片段{i}"
        parts.append(f"[{i}]《{title}》\n{item['content']}")
    return "\n\n".join(parts)
