# backend/api/main.py
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import os

from opensearchpy import OpenSearch

from db import init_db
from security import get_current_user, require_roles
from auth import router as auth_router

# ===================== Config =====================
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://opensearch:9200")
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASS = os.getenv("OPENSEARCH_PASS", "admin")
INDEX_NAME = os.getenv("INDEX_NAME", "news")

# ===================== App =====================
app = FastAPI(title="News Service")
app.include_router(auth_router)


@app.on_event("startup")
def _startup():
    init_db()


# ===================== OpenSearch client =====================
# Parse host/port from OPENSEARCH_URL (e.g. http://opensearch:9200)
_os_host = OPENSEARCH_URL.split("://")[1].split(":")[0]
_os_port = int(OPENSEARCH_URL.split(":")[-1])

os_client = OpenSearch(
    hosts=[{"host": _os_host, "port": _os_port}],
    http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
)


# ===================== Models =====================
class NewsIn(BaseModel):
    title: str
    summary: str
    content: str
    category: str
    published_at: datetime


# ===================== Helpers =====================
def _source_with_iso(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Đảm bảo published_at là ISO string khi trả về.
    """
    out = dict(doc)
    pa = out.get("published_at")
    if isinstance(pa, datetime):
        out["published_at"] = pa.isoformat()
    return out


def _category_query(category: str) -> Dict[str, Any]:
    """
    Trả về query lọc theo category, chịu được cả 2 kiểu mapping:
    - Có subfield keyword: category.keyword
    - Không có keyword: dùng match_phrase trên category
    """
    return {
        "bool": {
            "should": [
                {"term": {"category.keyword": category}},
                {"match_phrase": {"category": category}},
            ],
            "minimum_should_match": 1,
        }
    }


# ===================== Health =====================
@app.get("/health")
def health():
    info = os_client.info()
    return {"status": "ok", "cluster": info.get("cluster_name", "unknown")}


# ===================== CRUD =====================
@app.post("/news", tags=["news"])
def create_news(news: NewsIn, user=Depends(require_roles("admin", "reporter"))):
    doc = {
        "title": news.title,
        "summary": news.summary,
        "content": news.content,
        "category": news.category,
        "published_at": news.published_at.isoformat(),
        "author_id": user["id"],
    }
    res = os_client.index(index=INDEX_NAME, body=doc)
    return {"id": res["_id"], "result": res.get("result", "created")}


@app.put("/news/{id}", tags=["news"])
def update_news(id: str, news: NewsIn, user=Depends(get_current_user)):
    old = os_client.get(index=INDEX_NAME, id=id, ignore=[404])
    if not old or not old.get("found"):
        raise HTTPException(404, "Không tìm thấy tin")

    if user["role"] != "admin" and old["_source"].get("author_id") != user["id"]:
        raise HTTPException(403, "Bạn không có quyền sửa tin này")

    updated = {**old["_source"], **news.dict()}
    updated["published_at"] = news.published_at.isoformat()
    res = os_client.index(index=INDEX_NAME, id=id, body=updated)
    return {"id": id, "result": res.get("result", "updated")}


@app.get("/news/counters", tags=["news"])
def news_counters():
    """
    Đếm số bài theo từng danh mục + tổng (để hiển thị số trên chip).
    Ưu tiên dùng aggregation trên `category.keyword`.
    Nếu index KHÔNG có `category.keyword`, fallback sang `category`.
    Nếu vẫn lỗi -> quét toàn bộ và tự cộng dồn.
    """
    # 1) Thử agg trên category.keyword
    for field in ["category.keyword", "category"]:
        try:
            aggs = {"by_cat": {"terms": {"field": field, "size": 1000}}}
            res = os_client.search(index=INDEX_NAME, body={"size": 0, "aggs": aggs})
            buckets = res.get("aggregations", {}).get("by_cat", {}).get("buckets", [])
            if buckets:
                out = {b["key"]: b["doc_count"] for b in buckets}
                total = sum(out.values())
                return {"total": total, "by_category": out}
        except Exception:
            continue

    # 2) Fallback: đếm bằng cách quét toàn bộ (phù hợp với data nhỏ/medium)
    counts: Dict[str, int] = {}
    total = 0
    from_ = 0
    size = 1000  # mỗi trang 1000 bản ghi

    while True:
        q = {
            "query": {"match_all": {}},
            "sort": [{"published_at": {"order": "desc"}}],
            "size": size,
            "from": from_,
        }
        res = os_client.search(index=INDEX_NAME, body=q)
        hits = res.get("hits", {}).get("hits", [])
        if not hits:
            break

        for h in hits:
            src = h.get("_source", {}) or {}
            cat = src.get("category") or ""
            counts[cat] = (counts.get(cat, 0) + 1)
            total += 1

        if len(hits) < size:
            break
        from_ += size

    return {"total": total, "by_category": counts}


@app.get("/news/{id}", tags=["news"])
def get_news(id: str):
    res = os_client.get(index=INDEX_NAME, id=id, ignore=[404])
    if not res or not res.get("found"):
        raise HTTPException(404, "Không tìm thấy tin")
    return _source_with_iso(res["_source"])


@app.delete("/news/{id}", tags=["news"])
def delete_news(id: str, user=Depends(get_current_user)):
    doc = os_client.get(index=INDEX_NAME, id=id, ignore=[404])
    if not doc or not doc.get("found"):
        raise HTTPException(404, "Không tìm thấy tin")

    if user["role"] != "admin" and doc["_source"].get("author_id") != user["id"]:
        raise HTTPException(403, "Bạn không có quyền xoá")

    os_client.delete(index=INDEX_NAME, id=id)
    return {"deleted": id}


# ===================== LIST & FILTER =====================
@app.get("/news", tags=["news"])
def list_news(
    category: Optional[str] = Query(None),
    size: int = Query(50, le=200),
    from_: int = Query(0, alias="from"),
) -> List[Dict[str, Any]]:
    """
    Trả toàn bộ bài (match_all) hoặc lọc theo category nếu có ?category=...
    """
    if category:
        q = {"query": _category_query(category)}
    else:
        q = {"query": {"match_all": {}}}

    q["sort"] = [{"published_at": {"order": "desc"}}]
    q["size"] = size
    q["from"] = from_

    res = os_client.search(index=INDEX_NAME, body=q)
    return [{"id": h["_id"], "source": _source_with_iso(h["_source"])} for h in res["hits"]["hits"]]


@app.get("/news/category/{category}", tags=["news"])
def news_by_category(
    category: str, size: int = Query(50, le=200), from_: int = Query(0, alias="from")
):
    """
    Lọc thuần theo danh mục (phục vụ các chip Thế giới/Công nghệ/…).
    """
    q = {
        "query": _category_query(category),
        "sort": [{"published_at": {"order": "desc"}}],
        "size": size,
        "from": from_,
    }
    res = os_client.search(index=INDEX_NAME, body=q)
    return [{"id": h["_id"], "source": _source_with_iso(h["_source"])} for h in res["hits"]["hits"]]


# ===================== SEARCH =====================
@app.get("/search", tags=["news"])
def search(
    q: Optional[str] = Query(None),
    size: int = Query(10, le=100),
    from_: int = Query(0, alias="from"),
    category: Optional[str] = None,
):
    """
    Tìm theo từ khoá (title/summary/content).
    Nếu có category thì kết hợp lọc category.
    Nếu không có gì -> match_all.
    """
    must: List[Dict[str, Any]] = []

    if q:
        must.append(
            {
                "multi_match": {
                    "query": q,
                    "fields": ["title^3", "summary^2", "content"],
                }
            }
        )

    if category:
        must.append(_category_query(category))

    if not must:
        query = {"query": {"match_all": {}}}
    else:
        query = {"query": {"bool": {"must": must}}}

    query["sort"] = [{"published_at": {"order": "desc"}}]
    query["size"] = size
    query["from"] = from_

    res = os_client.search(index=INDEX_NAME, body=query)
    return {
        "total": res["hits"]["total"]["value"],
        "hits": [
            {
                "id": h["_id"],
                "score": h.get("_score"),
                "source": _source_with_iso(h["_source"]),
            }
            for h in res["hits"]["hits"]
        ],
    }
